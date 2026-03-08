"""
Hebrew Calendar Events Integration for Home Assistant
=====================================================
אינטגרציה לניהול אירועים בלוח שנה עברי.

מאפשרת:
- ניהול אירועים עם תאריכים עבריים (הוספה, עריכה, מחיקה)
- הגדרת תזכורות לפני כל אירוע
- הפעלת אוטומציות על בסיס אירועים ותזכורות
- שיתוף עם Google Calendar ו-Outlook
- הצגה בכרטיס Lovelace
"""

import logging
from datetime import date, timedelta
from pathlib import Path
from .Event import Event

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_time_change
from homeassistant.components.http import StaticPathConfig

from .const import (
    DOMAIN,
    CONF_EVENTS,
    EVENT_TRIGGER,
    REMINDER_TRIGGER,
    SERVICE_ADD_EVENT,
    SERVICE_EDIT_EVENT,
    SERVICE_REMOVE_EVENT,
    SERVICE_ADD_REMINDER,
    SERVICE_REMOVE_REMINDER,
    ATTR_EVENT_ID,
    ATTR_EVENT_NAME,
    ATTR_EVENT_TYPE,
    ATTR_HEBREW_DAY,
    ATTR_HEBREW_MONTH,
    ATTR_HEBREW_YEAR,
    ATTR_IS_RECURRING,
    ATTR_REMINDERS,
    ATTR_REMINDER_DAYS,
)
from .storage import HebrewCalendarStorage
from .HebrewDateConverter import HebrewDateConverter

_LOGGER = logging.getLogger(__name__)

# סכמת ולידציה להוספת/עריכת אירוע
EVENT_SCHEMA = vol.Schema({
    vol.Required(ATTR_EVENT_NAME): cv.string,
    vol.Required(ATTR_EVENT_TYPE): cv.string,
    vol.Required(ATTR_HEBREW_DAY): vol.All(int, vol.Range(min=1, max=31)),
    vol.Required(ATTR_HEBREW_MONTH): vol.All(int, vol.Range(min=1, max=13)),
    vol.Optional(ATTR_HEBREW_YEAR): vol.Any(None, int),
    vol.Optional(ATTR_IS_RECURRING, default=True): cv.boolean,
    vol.Optional(ATTR_REMINDERS, default=[]): [vol.All(int, vol.Range(min=0))],
})

EDIT_EVENT_SCHEMA = EVENT_SCHEMA.extend({
    vol.Required(ATTR_EVENT_ID): cv.string,
})

REMOVE_EVENT_SCHEMA = vol.Schema({
    vol.Required(ATTR_EVENT_ID): cv.string,
})

ADD_REMINDER_SCHEMA = vol.Schema({
    vol.Required(ATTR_EVENT_ID): cv.string,
    vol.Required(ATTR_REMINDER_DAYS): vol.All(int, vol.Range(min=0)),
})
REMOVE_REMINDER_SCHEMA = vol.Schema({
    vol.Required(ATTR_EVENT_ID): cv.string,
    vol.Required(ATTR_REMINDER_DAYS): vol.All(int, vol.Range(min=0)),
})


async def _async_register_lovelace_resource(hass, url: str) -> None:
    """רושם את קובץ ה-JS ישירות ב-Lovelace resources storage."""
    from homeassistant.components.lovelace import _async_get_component
    try:
        lovelace = _async_get_component(hass)
        resources = lovelace.resources
        await resources.async_load()
        existing = [r["url"] for r in resources.async_items()]
        if not any(url in u for u in existing):
            await resources.async_create_item({"res_type": "module", "url": url})
            _LOGGER.info("Registered Lovelace resource: %s", url)
        else:
            _LOGGER.debug("Lovelace resource already registered: %s", url)
    except Exception as e:
        _LOGGER.warning("Could not register Lovelace resource automatically: %s", e)
        _LOGGER.warning("Please add manually: Settings -> Dashboards -> Resources -> %s", url)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """
    הגדרה ראשונית של הדומיין.
    נקרא פעם אחת כשה-integration נטען.
    """
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    הגדרת entry של ה-integration.
    נקרא כשמוסיפים את ה-integration דרך ה-UI.
    מאתחל את האחסון, רושם שירותים, ומגדיר בדיקת אירועים יומית.
    """
    _LOGGER.info("Setting up Hebrew Calendar Events integration")

    # רישום קובץ ה-JS של הכרטיס כ-resource אוטומטי ב-Lovelace
    await hass.http.async_register_static_paths([
        StaticPathConfig(
            url_path="/hebrew_calendar/hebrew-calendar-card.js",
            path=Path(__file__).parent / "www" / "hebrew-calendar-card.js",
            cache_headers=False,
        )
    ])

    # רישום ישיר ב-Lovelace resources (הדרך האמינה ביותר)
    await _async_register_lovelace_resource(
        hass, "/hebrew_calendar/www/hebrew-calendar-card.js"
        )

    storage = HebrewCalendarStorage(hass)
    await storage.async_load()

    hass.data[DOMAIN][entry.entry_id] = {"storage": storage}

    # רישום שירותי ניהול אירועים
    _register_services(hass, entry)

    # הגדרת בדיקה יומית של אירועים ותזכורות (מתבצעת בחצות)
    async_track_time_change(
        hass,
        lambda now: hass.async_create_task(_check_events_and_reminders(hass, entry)),
        hour=0, minute=0, second=0,
    )

    # בדיקה ראשונית בהפעלה
    await _check_events_and_reminders(hass, entry)

    # פרסום platforms (sensor)
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "calendar"])

    _LOGGER.info("Hebrew Calendar Events integration setup complete")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    הסרת ה-integration.
    מנקה את הנתונים מהזיכרון.
    """
    await hass.config_entries.async_unload_platforms(entry, ["sensor", "calendar"])
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True


def _register_services(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """
    רישום כל שירותי ה-HA עבור ניהול אירועים.
    מאפשר קריאה לשירותים מאוטומציות ומה-UI.
    """

    async def handle_add_event(call: ServiceCall) -> None:
        """הוספת אירוע חדש ללוח השנה."""
        storage: HebrewCalendarStorage = hass.data[DOMAIN][entry.entry_id]["storage"]
        event_data = {k: call.data[k] for k in call.data}
        event_id = await storage.async_add_event(event_data)
        _LOGGER.info("Added Hebrew calendar event: %s (ID: %s)", event_data.get(ATTR_EVENT_NAME), event_id)
        # עדכון ה-sensor
        hass.bus.async_fire(f"{DOMAIN}_events_updated", {"entry_id": entry.entry_id})

    async def handle_edit_event(call: ServiceCall) -> None:
        """עריכת אירוע קיים לפי מזהה."""
        storage: HebrewCalendarStorage = hass.data[DOMAIN][entry.entry_id]["storage"]
        event_id = call.data[ATTR_EVENT_ID]
        event_data = {k: v for k, v in call.data.items() if k != ATTR_EVENT_ID}
        await storage.async_edit_event(event_id, event_data)
        _LOGGER.info("Edited Hebrew calendar event: %s", event_id)
        hass.bus.async_fire(f"{DOMAIN}_events_updated", {"entry_id": entry.entry_id})

    async def handle_remove_event(call: ServiceCall) -> None:
        """מחיקת אירוע לפי מזהה."""
        storage: HebrewCalendarStorage = hass.data[DOMAIN][entry.entry_id]["storage"]
        event_id = call.data[ATTR_EVENT_ID]
        await storage.async_remove_event(event_id)
        _LOGGER.info("Removed Hebrew calendar event: %s", event_id)
        hass.bus.async_fire(f"{DOMAIN}_events_updated", {"entry_id": entry.entry_id})

    async def handle_add_reminder(call: ServiceCall) -> None:
        """הוספת תזכורת לאירוע קיים."""
        storage: HebrewCalendarStorage = hass.data[DOMAIN][entry.entry_id]["storage"]
        await storage.async_add_reminder(call.data[ATTR_EVENT_ID], call.data[ATTR_REMINDER_DAYS])
        _LOGGER.info("Added reminder (%d days) to event %s", call.data[ATTR_REMINDER_DAYS], call.data[ATTR_EVENT_ID])
        hass.bus.async_fire(f"{DOMAIN}_events_updated", {"entry_id": entry.entry_id})

    async def handle_remove_reminder(call: ServiceCall) -> None:
        """הסרת תזכורת מאירוע קיים."""
        storage: HebrewCalendarStorage = hass.data[DOMAIN][entry.entry_id]["storage"]
        await storage.async_remove_reminder(call.data[ATTR_EVENT_ID], call.data[ATTR_REMINDER_DAYS])
        _LOGGER.info("Removed reminder (%d days) from event %s", call.data[ATTR_REMINDER_DAYS], call.data[ATTR_EVENT_ID])
        hass.bus.async_fire(f"{DOMAIN}_events_updated", {"entry_id": entry.entry_id})

    # רישום השירותים ב-HA
    hass.services.async_register(DOMAIN, SERVICE_ADD_EVENT, handle_add_event, schema=EVENT_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_EDIT_EVENT, handle_edit_event, schema=EDIT_EVENT_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_REMOVE_EVENT, handle_remove_event, schema=REMOVE_EVENT_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_ADD_REMINDER, handle_add_reminder, schema=ADD_REMINDER_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_REMOVE_REMINDER, handle_remove_reminder, schema=REMOVE_REMINDER_SCHEMA)


async def _check_events_and_reminders(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """
    בדיקה יומית של כל האירועים.
    מפעילה אירועי HA (triggers) עבור:
    - אירועים שמתרחשים היום
    - תזכורות שמתאימות להיום (N ימים לפני האירוע)
    """
    storage: HebrewCalendarStorage = hass.data[DOMAIN][entry.entry_id]["storage"]

    today_gregorian = date.today()
    today_hebrew = HebrewDateConverter.gregorianToHebrew(today_gregorian)

    events = await storage.async_get_events()

    for event in events:
        event_hebrew_day = event.hebrew_day
        event_hebrew_month = event.hebrew_month
        is_recurring = event.is_recurring
        event_hebrew_year = event.hebrew_year

        try:
            year_to_check = today_hebrew["year"] if is_recurring else event_hebrew_year
            if year_to_check is None:
                continue

            if not HebrewDateConverter.isValidHebrewMonthInYear(event_hebrew_month, year_to_check):
                continue

            actual_day = HebrewDateConverter.getValidDay(event_hebrew_day, event_hebrew_month, year_to_check)

            event_gregorian = HebrewDateConverter.hebrewToGregorian(
                actual_day, event_hebrew_month, year_to_check
            )

            if event_gregorian == today_gregorian:
                _LOGGER.info("Firing event trigger for: %s", event.event_name or "unknown")
                hass.bus.async_fire(
                    EVENT_TRIGGER,
                    {
                        "event_id": event.id,
                        "event_name": event.event_name,
                        "event_type": event.event_type,
                        "hebrew_date": f"{actual_day}/{event_hebrew_month}/{year_to_check}",
                        "gregorian_date": str(today_gregorian),
                        "is_recurring": is_recurring,
                    },
                )

            for reminder_days in event.reminders:
                if reminder_days == 0:
                    continue
                reminder_date = event_gregorian - timedelta(days=reminder_days)
                if reminder_date == today_gregorian:
                    _LOGGER.info(
                        "Firing reminder trigger for: %s (%d days before)",
                        event.event_name,
                        reminder_days,
                    )
                    hass.bus.async_fire(
                        REMINDER_TRIGGER,
                        {
                            "event_id": event.id,
                            "event_name": event.event_name,
                            "event_type": event.event_type,
                            "days_until_event": reminder_days,
                            "event_hebrew_date": f"{actual_day}/{event_hebrew_month}/{year_to_check}",
                            "event_gregorian_date": str(event_gregorian),
                            "reminder_days": reminder_days,
                        },
                    )

        except Exception as e:
            _LOGGER.error("Error processing event %s: %s", event.event_name or "unknown", e)