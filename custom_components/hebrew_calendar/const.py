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
    1: "תשרי",
    2: "חשון",
    3: "כסלו",
    4: "טבת",
    5: "שבט",
    6: "אדר",
    7: "אדר א׳",
    8: "אדר ב׳",
    9: "ניסן",
    10: "אייר",
    11: "סיון",
    12: "תמוז",
    13: "אב",
    14: "אלול",
}

# מפתח אחסון
STORAGE_KEY = f"{DOMAIN}_events"
STORAGE_VERSION = 1
