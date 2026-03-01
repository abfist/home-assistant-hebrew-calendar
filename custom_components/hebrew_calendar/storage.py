"""
Hebrew Calendar Storage
========================
מודול אחסון לשמירת האירועים בקובץ JSON מתמיד.
משתמש ב-HA Storage API לשמירה מאובטחת.

מאפשר: טעינה, שמירה, הוספה, עריכה, מחיקה של אירועים ותזכורות.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION, ATTR_REMINDERS

_LOGGER = logging.getLogger(__name__)


class HebrewCalendarStorage:
    """
    מנהל האחסון של האירועים.
    שומר את כל האירועים בקובץ JSON ב-.storage של HA.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """
        אתחול מנהל האחסון.
        
        Args:
            hass: מופע Home Assistant
        """
        self._hass = hass
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._events: Dict[str, Dict[str, Any]] = {}

    async def async_load(self) -> None:
        """
        טעינת האירועים מהאחסון.
        אם אין נתונים קיימים, מתחיל עם רשימה ריקה.
        """
        data = await self._store.async_load()
        if data is not None:
            self._events = data.get("events", {})
            _LOGGER.info("Loaded %d Hebrew calendar events from storage", len(self._events))
        else:
            self._events = {}
            _LOGGER.info("No stored events found, starting with empty list")

    async def async_save(self) -> None:
        """שמירת כל האירועים לאחסון."""
        await self._store.async_save({"events": self._events})

    async def async_get_events(self) -> List[Dict[str, Any]]:
        """
        קבלת רשימת כל האירועים.
        
        Returns:
            רשימת dicts, כל dict מייצג אירוע
        """
        return list(self._events.values())

    async def async_get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        קבלת אירוע בודד לפי מזהה.
        
        Args:
            event_id: מזהה האירוע
            
        Returns:
            dict האירוע, או None אם לא נמצא
        """
        return self._events.get(event_id)

    async def async_add_event(self, event_data: Dict[str, Any]) -> str:
        """
        הוספת אירוע חדש.
        
        Args:
            event_data: נתוני האירוע (ללא ID - יווצר אוטומטית)
            
        Returns:
            מזהה האירוע החדש
        """
        event_id = str(uuid.uuid4())
        event = {
            "id": event_id,
            **event_data,
            ATTR_REMINDERS: list(set(event_data.get(ATTR_REMINDERS, []))),  # הסרת כפילויות
        }
        self._events[event_id] = event
        await self.async_save()
        return event_id

    async def async_edit_event(self, event_id: str, event_data: Dict[str, Any]) -> bool:
        """
        עריכת אירוע קיים.
        
        Args:
            event_id: מזהה האירוע לעריכה
            event_data: הנתונים החדשים
            
        Returns:
            True אם הצליח, False אם האירוע לא נמצא
        """
        if event_id not in self._events:
            _LOGGER.warning("Tried to edit non-existent event: %s", event_id)
            return False
        
        # שמירת ה-ID המקורי
        existing = self._events[event_id]
        self._events[event_id] = {
            "id": event_id,
            **event_data,
            ATTR_REMINDERS: list(set(event_data.get(ATTR_REMINDERS, existing.get(ATTR_REMINDERS, [])))),
        }
        await self.async_save()
        return True

    async def async_remove_event(self, event_id: str) -> bool:
        """
        מחיקת אירוע.
        
        Args:
            event_id: מזהה האירוע למחיקה
            
        Returns:
            True אם הצליח, False אם האירוע לא נמצא
        """
        if event_id not in self._events:
            _LOGGER.warning("Tried to remove non-existent event: %s", event_id)
            return False
        
        del self._events[event_id]
        await self.async_save()
        return True

    async def async_add_reminder(self, event_id: str, days: int) -> bool:
        """
        הוספת תזכורת לאירוע.
        
        Args:
            event_id: מזהה האירוע
            days: מספר ימים לפני האירוע לתזכורת
            
        Returns:
            True אם הצליח
        """
        if event_id not in self._events:
            _LOGGER.warning("Tried to add reminder to non-existent event: %s", event_id)
            return False
        
        reminders = set(self._events[event_id].get(ATTR_REMINDERS, []))
        reminders.add(days)
        self._events[event_id][ATTR_REMINDERS] = sorted(list(reminders))
        await self.async_save()
        return True

    async def async_remove_reminder(self, event_id: str, days: int) -> bool:
        """
        הסרת תזכורת מאירוע.
        
        Args:
            event_id: מזהה האירוע
            days: מספר הימים של התזכורת להסרה
            
        Returns:
            True אם הצליח
        """
        if event_id not in self._events:
            _LOGGER.warning("Tried to remove reminder from non-existent event: %s", event_id)
            return False
        
        reminders = set(self._events[event_id].get(ATTR_REMINDERS, []))
        reminders.discard(days)
        self._events[event_id][ATTR_REMINDERS] = sorted(list(reminders))
        await self.async_save()
        return True

    def get_events_sync(self) -> List[Dict[str, Any]]:
        """
        קבלת רשימת אירועים בצורה סינכרונית (לשימוש ב-sensor).
        
        Returns:
            רשימת האירועים הנוכחית מהזיכרון
        """
        return list(self._events.values())
