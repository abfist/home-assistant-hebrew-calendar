"""
קבועים עבור Hebrew Calendar Events Integration
"""

# שם הדומיין - חייב להתאים לשם התיקייה
DOMAIN = "hebrew_calendar"

# מפתחות קונפיגורציה
CONF_EVENTS = "events"

# שמות שירותים
SERVICE_ADD_EVENT = "add_event"
SERVICE_EDIT_EVENT = "edit_event"
SERVICE_REMOVE_EVENT = "remove_event"
SERVICE_ADD_REMINDER = "add_reminder"
SERVICE_REMOVE_REMINDER = "remove_reminder"

# שמות אירועי HA (triggers)
EVENT_TRIGGER = f"{DOMAIN}_event_today"        # מופעל כשאירוע מתרחש היום
REMINDER_TRIGGER = f"{DOMAIN}_reminder_today"  # מופעל כשתזכורת מתרחשת היום

# שמות attributes
ATTR_EVENT_ID = "event_id"
ATTR_EVENT_NAME = "event_name"
ATTR_EVENT_TYPE = "event_type"
ATTR_HEBREW_DAY = "hebrew_day"
ATTR_HEBREW_MONTH = "hebrew_month"
ATTR_HEBREW_YEAR = "hebrew_year"
ATTR_IS_RECURRING = "is_recurring"
ATTR_REMINDERS = "reminders"
ATTR_REMINDER_DAYS = "reminder_days"

# סוגי אירועים מוכנים מראש
EVENT_TYPES = [
    "יום הולדת",
    "יארצייט",
    "יום נישואין",
    "חג",
    "אחר",
]

# שמות חודשים עבריים
HEBREW_MONTHS = {
    7: "תשרי",
    8: "חשון",
    9: "כסלו",
    10: "טבת",
    11: "שבט",
    12: "אדר",
    13: "אדר ב׳",
    1: "ניסן",
    2: "אייר",
    3: "סיון",
    4: "תמוז",
    5: "אב",
    6: "אלול",
}

# מפתח אחסון
STORAGE_KEY = f"{DOMAIN}_events"
STORAGE_VERSION = 1
