"""
Hebrew Calendar - Calendar Platform
=====================================
מממש את ה-calendar platform של HA.
מאפשר הצגת האירועים בלוח השנה המובנה של HA
ושיתוף עם Google Calendar / Outlook דרך HA integrations.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from .Event import Event

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
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
from .HebrewDateConverter import HebrewDateConverter

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """הגדרת calendar entity."""
    storage: HebrewCalendarStorage = hass.data[DOMAIN][entry.entry_id]["storage"]

    async_add_entities([HebrewCalendarEntity(hass, entry, storage)], True)


class HebrewCalendarEntity(CalendarEntity):
    """
    Calendar Entity עבור Hebrew Calendar Events.
    מציג את האירועים בלוח השנה של HA.
    ניתן לשתף דרך Google Calendar / Outlook integrations של HA.
    """

    _attr_icon = "mdi:calendar-star"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        storage: HebrewCalendarStorage,
    ) -> None:
        """אתחול."""
        self._hass = hass
        self._entry = entry
        self._storage = storage
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_name = "Hebrew Calendar"
        self._next_event: Optional[CalendarEvent] = None

    @property
    def event(self) -> Optional[CalendarEvent]:
        """האירוע הקרוב ביותר."""
        return self._next_event

    async def async_update(self) -> None:
        """עדכון: מחפש את האירוע הקרוב ביותר."""
        events = await self._get_events_in_range(
            date.today(),
            date.today() + timedelta(days=365),
        )
        self._next_event = events[0] if events else None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> List[CalendarEvent]:
        """
        קבלת כל האירועים בטווח תאריכים נתון.
        נקרא על ידי HA לצורך הצגה בלוח השנה.
        
        Args:
            start_date: תחילת הטווח
            end_date: סוף הטווח
            
        Returns:
            רשימת CalendarEvent objects
        """
        return await self._get_events_in_range(
            start_date.date() if isinstance(start_date, datetime) else start_date,
            end_date.date() if isinstance(end_date, datetime) else end_date,
        )

    async def _get_events_in_range(
        self, start: date, end: date
    ) -> List[CalendarEvent]:
        """
        מחפש אירועים בטווח תאריכים.
        
        Args:
            start: תחילת הטווח
            end: סוף הטווח
            
        Returns:
            רשימת CalendarEvent ממוינת לפי תאריך
        """
        storage_events = self._storage.get_events_sync()
        calendar_events = []

        for event in storage_events:
            try:
                gregorian_dates = self._get_event_dates_in_range(event, start, end)
                
                for event_date in gregorian_dates:
                    hebrew_day = event[ATTR_HEBREW_DAY]
                    hebrew_month = event[ATTR_HEBREW_MONTH]
                    hebrew_year = HebrewDateConverter.gregorianToHebrew(event_date)["year"]
                    
                    description = (
                        f"סוג: {event.get(ATTR_EVENT_TYPE, 'לא צוין')}\n"
                        f"תאריך עברי: {HebrewDateConverter.hebrewDateToString(hebrew_day, hebrew_month, hebrew_year)}\n"
                        f"{'אירוע חוזר' if event.get(ATTR_IS_RECURRING) else 'אירוע חד-פעמי'}"
                    )
                    
                    # הוספת תזכורות לתיאור
                    reminders = event.get(ATTR_REMINDERS, [])
                    if reminders:
                        reminder_text = ", ".join(f"{r} ימים לפני" for r in sorted(reminders) if r > 0)
                        if reminder_text:
                            description += f"\nתזכורות: {reminder_text}"
                    
                    calendar_events.append(
                        CalendarEvent(
                            start=event_date,
                            end=event_date + timedelta(days=1),
                            summary=event[ATTR_EVENT_NAME],
                            description=description,
                        )
                    )
            except Exception as e:
                _LOGGER.debug("Error processing event for calendar: %s", e)

        calendar_events.sort(key=lambda e: e.start)
        return calendar_events

    def _get_event_dates_in_range(
        self, event: Dict[str, Any], start: date, end: date
    ) -> List[date]:
        """
        מחזיר את כל התאריכים של אירוע בטווח נתון.
        עבור אירועים חוזרים, בודק את כל השנים בטווח.
        
        Args:
            event: נתוני האירוע
            start: תחילת הטווח
            end: סוף הטווח
            
        Returns:
            רשימת תאריכים גרגוריאניים
        """
        dates = []
        is_recurring = event.get(ATTR_IS_RECURRING, True)
        
        if not is_recurring:
            # אירוע חד-פעמי
            event_year = event.get(ATTR_HEBREW_YEAR)
            if event_year:
                try:
                    event_date = HebrewDateConverter.hebrewToGregorian(
                        event[ATTR_HEBREW_DAY], event[ATTR_HEBREW_MONTH], event_year
                    )
                    if start <= event_date <= end:
                        dates.append(event_date)
                except Exception:
                    pass
        else:
            # אירוע חוזר - בדיקה לכל שנה בטווח
            start_hebrew = HebrewDateConverter.gregorianToHebrew(start)
            end_hebrew = HebrewDateConverter.gregorianToHebrew(end)
            
            for year in range(start_hebrew["year"], end_hebrew["year"] + 2):
                try:
                    event_date = HebrewDateConverter.hebrewToGregorian(
                        event[ATTR_HEBREW_DAY], event[ATTR_HEBREW_MONTH], year
                    )
                    if start <= event_date <= end:
                        dates.append(event_date)
                except Exception:
                    pass
        
        return dates