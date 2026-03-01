# Hebrew Calendar Events Integration for Home Assistant

אינטגרציה לניהול אירועים עם תאריכים עבריים ב-Home Assistant.

[![HACS Custom][hacs-badge]](https://hacs.xyz)
[![Version][version-badge]](https://github.com/your-repo/hebrew-calendar-ha)

---

## תכונות

- 📅 ניהול מלא של אירועים עם תאריכים עבריים
- 🔔 תזכורות מרובות לכל אירוע (N ימים לפני)
- 🔄 תמיכה באירועים חוזרים ואירועים חד-פעמיים
- ⚡ Triggers לאוטומציות בזמן האירוע ובזמן התזכורת
- 🖥️ כרטיס Lovelace מובנה לניהול אירועים
- 📆 אינטגרציה עם לוח השנה הפנימי של HA
- 🌐 תמיכה בשיתוף עם Google Calendar ו-Outlook

---

## התקנה דרך HACS

1. פתח HACS ב-Home Assistant
2. לחץ על "Integrations" ואז על "Explore & Download Repositories"
3. חפש "Hebrew Calendar Events"
4. לחץ "Download"
5. הפעל מחדש את HA

### התקנה ידנית

1. העתק את תיקיית `custom_components/hebrew_calendar` לתוך `custom_components/` של HA
2. העתק את `www/hebrew-calendar-card.js` לתוך `www/` של HA
3. הפעל מחדש את HA

---

## הגדרה

1. עבור ל-Settings > Integrations > Add Integration
2. חפש "Hebrew Calendar Events"
3. לחץ "Submit"

### הוספת הכרטיס ל-Lovelace

הוסף ב-resources:
```yaml
resources:
  - url: /local/hebrew-calendar-card.js
    type: module
```

הוסף כרטיס:
```yaml
type: custom:hebrew-calendar-card
entity: sensor.hebrew_calendar_events
title: לוח שנה עברי
```

---

## שירותים

### `hebrew_calendar.add_event` - הוספת אירוע

```yaml
service: hebrew_calendar.add_event
data:
  event_name: "יום הולדת יוסי"
  event_type: "יום הולדת"
  hebrew_day: 15
  hebrew_month: 1        # 1=תשרי
  is_recurring: true
  reminders: [7, 1]      # תזכורת שבוע לפני ויום לפני
```

### `hebrew_calendar.edit_event` - עריכת אירוע

```yaml
service: hebrew_calendar.edit_event
data:
  event_id: "a1b2c3d4-..."
  event_name: "שם חדש"
  event_type: "יום הולדת"
  hebrew_day: 15
  hebrew_month: 1
  is_recurring: true
  reminders: [7]
```

### `hebrew_calendar.remove_event` - מחיקת אירוע

```yaml
service: hebrew_calendar.remove_event
data:
  event_id: "a1b2c3d4-..."
```

### `hebrew_calendar.add_reminder` - הוספת תזכורת

```yaml
service: hebrew_calendar.add_reminder
data:
  event_id: "a1b2c3d4-..."
  reminder_days: 7
```

### `hebrew_calendar.remove_reminder` - הסרת תזכורת

```yaml
service: hebrew_calendar.remove_reminder
data:
  event_id: "a1b2c3d4-..."
  reminder_days: 7
```

---

## Triggers לאוטומציות

### אירוע מתרחש היום

האירוע `hebrew_calendar_event_today` מופעל בחצות כל יום עבור כל אירוע שמתרחש באותו יום.

```yaml
automation:
  trigger:
    platform: event
    event_type: hebrew_calendar_event_today
  action:
    service: notify.mobile_app
    data:
      message: "היום הוא {{ trigger.event.data.event_name }}!"
```

**נתונים זמינים ב-trigger.event.data:**
| שדה | תיאור |
|-----|-------|
| `event_id` | מזהה ייחודי של האירוע |
| `event_name` | שם האירוע |
| `event_type` | סוג האירוע |
| `hebrew_date` | תאריך עברי כמחרוזת |
| `gregorian_date` | תאריך גרגוריאני |
| `is_recurring` | האם האירוע חוזר |

### תזכורת לאירוע

האירוע `hebrew_calendar_reminder_today` מופעל בחצות ביום שמתאים לתזכורת.

```yaml
automation:
  trigger:
    platform: event
    event_type: hebrew_calendar_reminder_today
  action:
    service: notify.mobile_app
    data:
      message: >
        תזכורת: {{ trigger.event.data.event_name }}
        בעוד {{ trigger.event.data.days_until_event }} ימים
        ({{ trigger.event.data.event_gregorian_date }})
```

**נתונים זמינים ב-trigger.event.data:**
| שדה | תיאור |
|-----|-------|
| `event_id` | מזהה האירוע |
| `event_name` | שם האירוע |
| `event_type` | סוג האירוע |
| `days_until_event` | כמה ימים עד האירוע |
| `event_hebrew_date` | תאריך עברי של האירוע |
| `event_gregorian_date` | תאריך גרגוריאני של האירוע |
| `reminder_days` | הגדרת התזכורת (X ימים לפני) |

### סינון לפי סוג אירוע

ניתן לסנן triggers לפי סוג אירוע ספציפי:

```yaml
automation:
  trigger:
    platform: event
    event_type: hebrew_calendar_event_today
    event_data:
      event_type: "יארצייט"   # רק יארצייטים
  action:
    service: notify.mobile_app
    data:
      message: "יארצייט: {{ trigger.event.data.event_name }}"
```

### דוגמת אוטומציה מלאה

```yaml
# שליחת הודעה 7 ימים לפני יום הולדת
automation:
  alias: "תזכורת יום הולדת שבועית"
  trigger:
    platform: event
    event_type: hebrew_calendar_reminder_today
  condition:
    - condition: template
      value_template: >
        {{ trigger.event.data.event_type == 'יום הולדת'
           and trigger.event.data.days_until_event == 7 }}
  action:
    - service: notify.family_group
      data:
        title: "🎂 יום הולדת מתקרב!"
        message: >
          בעוד שבוע: {{ trigger.event.data.event_name }}
          תאריך: {{ trigger.event.data.event_gregorian_date }}
```

---

## Sensors

| Entity | תיאור |
|--------|-------|
| `sensor.hebrew_calendar_events` | כל האירועים + state = מספר כולל |
| `sensor.hebrew_calendar_today` | אירועי היום |
| `sensor.hebrew_calendar_upcoming` | אירועים ב-30 ימים הקרובים |
| `calendar.hebrew_calendar` | לוח שנה מלא לשיתוף עם Google/Outlook |

---

## שיתוף עם Google Calendar / Outlook

האינטגרציה יוצרת `calendar.hebrew_calendar`. על מנת לשתף:

**Google Calendar:**
1. התקן את ה-Google Calendar integration
2. קשר את `calendar.hebrew_calendar` לחשבון Google שלך

**Outlook:**
1. התקן את ה-Microsoft 365 integration
2. קשר את `calendar.hebrew_calendar` לחשבון Microsoft שלך

---

## דרישות

- Home Assistant 2023.1.0 ומעלה
- Python package: `pyluach` (מותקן אוטומטית)

---

## מבנה הקבצים

```
custom_components/hebrew_calendar/
├── __init__.py          # לוגיקה ראשית, רישום שירותים, triggers
├── config_flow.py       # הגדרה דרך UI
├── const.py             # קבועים
├── sensor.py            # sensor platforms
├── calendar.py          # calendar platform
├── storage.py           # אחסון מתמיד
├── hebrew_date.py       # המרת תאריכים עברי-גרגוריאני
├── services.yaml        # הגדרות שירותים
├── manifest.json        # מטא-דאטה
└── translations/
    ├── he.json
    └── en.json

www/
└── hebrew-calendar-card.js   # כרטיס Lovelace
```

---

## חודשים עבריים

| מספר | שם |
|------|----|
| 1 | תשרי |
| 2 | חשון |
| 3 | כסלו |
| 4 | טבת |
| 5 | שבט |
| 6 | אדר (בשנה פשוטה) |
| 7 | ניסן |
| 8 | אייר |
| 9 | סיון |
| 10 | תמוז |
| 11 | אב |
| 12 | אלול |
| 13 | אדר ב׳ (בשנה מעוברת) |

---

## רישיון

MIT License

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-orange.svg
[version-badge]: https://img.shields.io/badge/version-1.0.0-blue.svg
