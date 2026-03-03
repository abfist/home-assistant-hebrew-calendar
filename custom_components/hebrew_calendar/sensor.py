"""
Hebrew Calendar Sensor Platform
================================
מגדיר sensors עבור ה-integration:
- sensor.hebrew_calendar_events: רשימת כל האירועים
- sensor.hebrew_calendar_today: אירועים שמתרחשים היום
- sensor.hebrew_calendar_upcoming: אירועים קרובים (30 ימים)

ה-sensors מתעדכנים אוטומטית כשאירועים מתווספים/נמחקים/נערכים.
"""

import logging
import copy
from Event import Event
from datetime import date, timedelta
from typing import Any, Dict, List, Optional
from HebrewDateConverter import HebrewDateConverter

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    ATTR_EVENT_NAME,
    ATTR_EVENT_TYPE,
    ATTR_HEBREW_DAY,
    ATTR_HEBREW_MONTH,
    ATTR_HEBREW_YEAR,
    ATTR_IS_RECURRING,
    ATTR_REMINDERS,
)
from .storage import HebrewCalendarStorage
# from .hebrew_date import HebrewDateConverter

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    הגדרת sensors עבור ה-entry.
    יוצר שלושה sensors: כל האירועים, היום, קרובים.
    """
    storage: HebrewCalendarStorage = hass.data[DOMAIN][entry.entry_id]["storage"]
    # converter: HebrewDateConverter = hass.data[DOMAIN][entry.entry_id]["converter"]

    entities = [
        HebrewCalendarAllEventsSensor(hass, entry, storage),
        HebrewCalendarTodaySensor(hass, entry, storage),
        HebrewCalendarUpcomingSensor(hass, entry, storage),
        HebrewCalendarTodayReminders(hass, entry, storage),
    ]

    async_add_entities(entities, True)

    # האזנה לאירועי עדכון ורענון ה-sensors
    @callback
    def _handle_events_updated(event):
        """עדכון כל ה-sensors כשהאירועים משתנים."""
        for entity in entities:
            entity.async_schedule_update_ha_state(True)

    hass.bus.async_listen(f"{DOMAIN}_events_updated", _handle_events_updated)


class HebrewCalendarBaseSensor(SensorEntity):
    """
    Sensor בסיסי לכל ה-sensors של ה-integration.
    מכיל לוגיקה משותפת.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        storage: HebrewCalendarStorage,
    ) -> None:
        """אתחול הסנסור."""
        self._hass = hass
        self._entry = entry
        self._storage = storage
        self._events: List[Event] = []


class HebrewCalendarAllEventsSensor(HebrewCalendarBaseSensor):
    """
    סנסור שמציג את כל האירועים.
    מספק את כל הנתונים ל-Lovelace card.
    """

    _attr_icon = "mdi:calendar-star"

    def __init__(self, *args, **kwargs) -> None:
        """אתחול."""
        super().__init__(*args, **kwargs)
        self._attr_unique_id = f"{self._entry.entry_id}_all_events"
        self._attr_name = "Hebrew Calendar Events"

    async def async_update(self) -> None:
        """עדכון נתוני הסנסור."""
        self._events = self._storage.get_events_sync()

    @property
    def state(self) -> int:
        """מספר האירועים הכולל."""
        return len(self._events)

    @property
    def extra_state_attributes(self) -> Event:
        """
        כל פרטי האירועים כ-attributes.
        משמש את ה-Lovelace card וה-automations.
        """
        enriched_events =copy.deepcopy(self._events)
        
        # מיון לפי מספר ימים עד האירוע
        enriched_events.sort(key=lambda e: (e["days_until"] is None, e.get("days_until", 9999)))
        
        return {
            "events": enriched_events,
            "total_count": len(enriched_events),
            "current_hebrew_date": HebrewDateConverter.getCurrentHebrewDate(),
        }


class HebrewCalendarTodaySensor(HebrewCalendarBaseSensor):
    """
    סנסור שמציג אירועים שמתרחשים היום.
    """

    _attr_icon = "mdi:calendar-today"

    def __init__(self, *args, **kwargs) -> None:
        """אתחול."""
        super().__init__(*args, **kwargs)
        self._attr_unique_id = f"{self._entry.entry_id}_today"
        self._attr_name = "Hebrew Calendar Today"
        self._today_events: List[Event] = []

    async def async_update(self) -> None:
        """עדכון: מחפש אירועים שמתרחשים היום."""
        all_events = self._storage.get_events_sync()

        self._today_events = []
        for event in all_events:
            if event.isToday():
                self._today_events.append({
                    **event,
                })

    @property
    def state(self) -> int:
        """מספר האירועים שמתרחשים היום."""
        return len(self._today_events)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """פרטי האירועים של היום."""
        return {"events_today": self._today_events}


class HebrewCalendarTodayReminders(HebrewCalendarBaseSensor):
    """
    סנסור שמציג אירועים להם יש תזכורת היום.
    """

    _attr_icon = "mdi:calendar-today"

    def __init__(self, *args, **kwargs) -> None:
        """אתחול."""
        super().__init__(*args, **kwargs)
        self._attr_unique_id = f"{self._entry.entry_id}_today"
        self._attr_name = "Hebrew Calendar Today"
        self._today_reminders: List[Event] = []

    async def async_update(self) -> None:
        """עדכון: מחפש אירועים שלהם יש תזכורת היום."""
        all_events = self._storage.get_events_sync()
        self._today_reminders = []
        for event in all_events:
            if event.isReminderToday():
                self._today_reminders.append({
                    **event
                })

    @property
    def state(self) -> int:
        """מספר האירועים שמתרחשים היום."""
        return len(self._today_reminders)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """פרטי האירועים של היום."""
        return {"events_today": self._today_reminders}


class HebrewCalendarUpcomingSensor(HebrewCalendarBaseSensor):
    """
    Sensor שמציג אירועים קרובים ב-30 הימים הבאים.
    """

    _attr_icon = "mdi:calendar-clock"

    def __init__(self, *args, **kwargs) -> None:
        """אתחול."""
        super().__init__(*args, **kwargs)
        self._attr_unique_id = f"{self._entry.entry_id}_upcoming"
        self._attr_name = "Hebrew Calendar Upcoming"
        self._upcoming_events: List[Dict[str, Any]] = []

    async def async_update(self) -> None:
        """עדכון: מחפש אירועים ב-30 הימים הקרובים."""
        all_events = self._storage.get_events_sync()
        today = date.today()
        future_limit = today + timedelta(days=30)
        today_hebrew = self._converter.gregorian_to_hebrew(today)
        
        self._upcoming_events = []
        for event in all_events:
            year = today_hebrew["year"] if event.get(ATTR_IS_RECURRING) else event.get(ATTR_HEBREW_YEAR)
            gregorian = self._get_event_gregorian_date(event, year)
            
            if gregorian and today <= gregorian <= future_limit:
                days_until = (gregorian - today).days
                self._upcoming_events.append({
                    **event,
                    "gregorian_date": str(gregorian),
                    "days_until": days_until,
                    "hebrew_date_string": self._converter.hebrew_date_to_string(
                        event[ATTR_HEBREW_DAY], event[ATTR_HEBREW_MONTH], year
                    ),
                })
        
        self._upcoming_events.sort(key=lambda e: e["days_until"])

    @property
    def state(self) -> int:
        """מספר האירועים הקרובים."""
        return len(self._upcoming_events)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """פרטי האירועים הקרובים."""
        return {"upcoming_events": self._upcoming_events}
