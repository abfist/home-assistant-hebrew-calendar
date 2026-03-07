"""
Hebrew Calendar Storage
========================
מודול אחסון לשמירת האירועים בקובץ JSON מתמיד.
משתמש ב-HA Storage API לשמירה מאובטחת.

מאפשר: טעינה, שמירה, הוספה, עריכה, מחיקה של אירועים ותזכורות.
"""
from .Event import Event
import logging
import uuid
from typing import Any, Dict, List, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION, ATTR_REMINDERS

from .HebrewDateConverter import HebrewDateConverter

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
        self._events: Dict[str, Event] = {}

    @staticmethod
    def validate_event_data(event_data: Dict[str, Any]) -> Optional[str]:
        """
        בדיקת תקינות נתוני אירוע לפני שמירה.
        
        Returns:
            מחרוזת שגיאה אם הנתונים לא תקינים, None אם תקין.
        """
        day = event_data.get("hebrew_day")
        month = event_data.get("hebrew_month")
        year = event_data.get("hebrew_year")
        is_recurring = event_data.get("is_recurring", True)

        if not (1 <= day <= 31):
            return f"יום לא חוקי: {day}. הטווח החוקי הוא 1–31."

        if not (1 <= month <= 13):
            return f"חודש לא חוקי: {month}. הטווח החוקי הוא 1–13."

        # לאירועים חד-פעמיים עם שנה: נבדוק שהתאריך קיים בפועל
        if not is_recurring and year:
            if not HebrewDateConverter.isValidHebrewMonthInYear(month, year):
                from .const import HEBREW_MONTHS
                month_name = HEBREW_MONTHS.get(month, str(month))
                return (
                    f"חודש {month_name} (חודש {month}) אינו קיים בשנה העברית {year}. "
                    f"ייתכן שניסית להוסיף אדר ב׳ בשנה שאינה שנת עיבור."
                )
            last_day = HebrewDateConverter.getLastDayOfHebrewMonth(month, year)
            if day > last_day:
                return (
                    f"יום {day} אינו קיים בחודש {month} בשנה {year}. "
                    f"החודש מכיל {last_day} ימים בלבד. "
                    f"שנה לאירוע חוזר כדי לאפשר התאמה אוטומטית, או בחר יום עד {last_day}."
                )

        # לאירועים חוזרים: בדוק שהיום אינו מעל 31 
        if day > 31:
            return f"יום {day} אינו חוקי. בלוח השנה העברי אין חודש עם יותר מ-31 ימים."

        # אזהרה (לא שגיאה) לאירועים חוזרים עם יום 30/31 — ייתכן שלא יחול בכל שנה
        # לא מחזירים שגיאה, אלא רושמים בלוג
        if is_recurring and day >= 30:
            _LOGGER.info(
                "Event with day 30||31 in month %d is recurring — in years where the month has only 29 days, "
                "the event will be observed on the 29th (last day of month).",
                month,
            )

        return None  # תקין

    async def async_load(self) -> None:
        """
        טעינת האירועים מהאחסון.
        אם אין נתונים קיימים, מתחיל עם רשימה ריקה.
        """
        data = await self._store.async_load()
        if data is not None:
            events=data.get("events", {})
            self._events: Dict[str, Event] = {}
            for key, value in events.items():
                self._events[key] = Event.fromDict(value)
        #     self._events = data.get("events", {})
            _LOGGER.info("Loaded %d Hebrew calendar events from storage", len(self._events))
        else:
            self._events = {}
            _LOGGER.info("No stored events found, starting with empty list")

    async def async_save(self) -> None:
        """שמירת כל האירועים לאחסון."""
        await self._store.async_save({"events": {k: v.as_dict() for k, v in self._events.items()}})

    async def async_get_events(self) -> List[Event]:
        """
        קבלת רשימת כל האירועים.
        
        Returns:
            רשימת ארועים
        """
        return Event.fromEventList(list(self._events.values()))

    async def async_get_event(self, event_id: str) -> Optional[Event]:
        """
        קבלת אירוע בודד לפי מזהה.
        
        Args:
            event_id: מזהה האירוע
            
        Returns:
            dict האירוע, או None אם לא נמצא
        """
        event = self._events.get(event_id)
        return Event.fromEvent(event) if event else None

    async def async_add_event(self, event_data: Dict[str,Any]) -> str:
        """
        הוספת אירוע חדש.
        
        Args:
            event_data: נתוני האירוע (ללא ID - יווצר אוטומטית)
            
        Returns:
            מזהה האירוע החדש
        """
        event_id = str(uuid.uuid4())
        validation_error = self.validate_event_data(event_data)
        if validation_error:
            _LOGGER.error("Invalid event data: %s", validation_error)
            raise ValueError(validation_error)
        event_data["id"] = event_id
        event_data[ATTR_REMINDERS]=list(set(event_data.get(ATTR_REMINDERS, [])))  # הסרת כפילויות
        self._events[event_id] = Event.fromDict(event_data)
        await self.async_save()
        return event_id

    async def async_edit_event(self, event_id: str, event_data: Event) -> bool:
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
        
        validation_error = self.validate_event_data(event_data)
        if validation_error:
            _LOGGER.error("Invalid event data on edit: %s", validation_error)
            raise ValueError(validation_error)

        # שמירת ה-ID המקורי
        existing = self._events[event_id]
        event_data["id"] = event_id
        self._events[event_id] = Event.fromDict(event_data)
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
        reminders = set(self._events[event_id].reminders)
        reminders.add(days)
        self._events[event_id].reminders = sorted(list(reminders))
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
        reminders = set(self._events[event_id].reminders)
        # reminders = set(self._events[event_id].get(ATTR_REMINDERS, []))
        reminders.discard(days)
        self._events[event_id].reminders = sorted(list(reminders))
        await self.async_save()
        return True

    def get_events_sync(self) -> List[Event]:
        """
        קבלת רשימת אירועים בצורה סינכרונית (לשימוש ב-sensor).
        
        Returns:
            רשימת האירועים הנוכחית מהזיכרון
        """
        return list(self._events.values())