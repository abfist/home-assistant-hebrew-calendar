# Hebrew Calendar Events

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/your-repo/hebrew-calendar-ha.svg)](https://github.com/your-repo/hebrew-calendar-ha/releases)
![Minimum HA Version](https://img.shields.io/badge/HA-2023.1.0%2B-blue)

A Home Assistant custom integration for managing events based on the **Hebrew (Jewish) calendar**. Track birthdays, yahrzeits, anniversaries, and other recurring or one-time events — all anchored to Hebrew dates, with automatic conversion to Gregorian dates, reminder support, and a custom Lovelace card.

---

## Features

- 📅 **Create, edit, and delete events** using Hebrew dates
- 🔁 **Recurring events** — automatically recalculates every year
- 🔔 **Reminders** — fire automation triggers N days before any event
- 📊 **Four sensors** exposing events to dashboards and automations
- 🗓️ **Calendar entity** — integrates with the HA calendar view and Google Calendar / Outlook
- 🃏 **Custom Lovelace card** (`hebrew-calendar-card`) included
- 🔧 **UI configuration** — set up entirely from Settings → Integrations, no YAML required

---

## Supported Event Types

| Type | Hebrew |
|------|--------|
| Birthday | יום הולדת |
| Yahrzeit | יארצייט |
| Anniversary | יום נישואין |
| Holiday | חג |
| Other | אחר |

---

## Installation

### HACS (Recommended)

1. Open **HACS** in your Home Assistant instance.
2. Go to **Integrations** → click the three-dot menu → **Custom repositories**.
3. Add the repository URL and select category **Integration**.
4. Search for **Hebrew Calendar Events** and click **Download**.
5. Restart Home Assistant.

### Manual

1. Copy the `hebrew_calendar` folder into your `config/custom_components/` directory.
2. Copy `hebrew-calendar-card.js` into your `config/www/` directory.
3. Restart Home Assistant.

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Hebrew Calendar Events** and click it.
3. Confirm the setup — no credentials or additional input required.

> Only one instance of this integration can be installed at a time.

---

## Sensors

The integration creates four sensor entities:

| Entity | Description | State |
|--------|-------------|-------|
| `sensor.hebrew_calendar_events` | All events | Total event count |
| `sensor.hebrew_calendar_today` | Events occurring today | Count of today's events |
| `sensor.hebrew_calendar_upcoming` | Events in the next 30 days | Count of upcoming events |
| `sensor.hebrew_calendar_reminders_today` | Events with a reminder due today | Count of reminders today |

### Sensor Attributes

Each sensor exposes its events as attributes. Every event object contains:

```yaml
id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
event_name: "Yossi's Birthday"
event_type: "יום הולדת"
hebrew_day: 15
hebrew_month: 1
hebrew_year: null          # null for recurring events
is_recurring: true
reminders: [7, 1]          # days before the event
hebrew_date_string: "ט״ו בתשרי תשפ״ה"
gregorian_date: "2024-10-17"
days_until: 12
```

All four sensors share the following top-level attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `total_count` | `int` | Number of events in this sensor |
| `has_events` | `bool` | `true` if `total_count > 0`, `false` otherwise |
| `current_hebrew_date` | `string` | Today's Hebrew date as a readable string |
| `summary` | `string` | Human-readable text summary of the events |

The `has_events` boolean is especially useful in automation conditions and Lovelace visibility rules — no need to compare numeric values.

Additional attributes per sensor:

| Sensor | Events attribute key | Extra attributes |
|--------|----------------------|-----------------|
| `sensor.hebrew_calendar_events` | `events` | — |
| `sensor.hebrew_calendar_today` | `events_today` | — |
| `sensor.hebrew_calendar_reminders_today` | `events_today` | — |
| `sensor.hebrew_calendar_upcoming` | `upcoming_events` | `closest_event`, `days until next event` |

---

## Services

### `hebrew_calendar.add_event`

Add a new event to the calendar.

| Field | Required | Description |
|-------|----------|-------------|
| `event_name` | ✅ | Display name of the event |
| `event_type` | ✅ | One of the predefined event types |
| `hebrew_day` | ✅ | Day in the Hebrew month (1–30) |
| `hebrew_month` | ✅ | Hebrew month (1–13) |
| `hebrew_year` | ❌ | Required only for one-time (non-recurring) events |
| `is_recurring` | ❌ | Whether the event repeats annually (default: `true`) |
| `reminders` | ❌ | List of days-before to trigger reminders, e.g. `[7, 1]` |

**Example:**

```yaml
service: hebrew_calendar.add_event
data:
  event_name: "Yossi's Birthday"
  event_type: "יום הולדת"
  hebrew_day: 15
  hebrew_month: 1
  is_recurring: true
  reminders:
    - 7
    - 1
```

---

### `hebrew_calendar.edit_event`

Edit an existing event by its ID.

| Field | Required | Description |
|-------|----------|-------------|
| `event_id` | ✅ | UUID of the event to edit |
| *(all other fields same as `add_event`)* | ✅ | |

---

### `hebrew_calendar.remove_event`

Remove an event by its ID.

| Field | Required | Description |
|-------|----------|-------------|
| `event_id` | ✅ | UUID of the event to remove |

---

### `hebrew_calendar.add_reminder`

Add a reminder to an existing event.

| Field | Required | Description |
|-------|----------|-------------|
| `event_id` | ✅ | UUID of the event |
| `reminder_days` | ✅ | Number of days before the event (0–365) |

---

### `hebrew_calendar.remove_reminder`

Remove a specific reminder from an event.

| Field | Required | Description |
|-------|----------|-------------|
| `event_id` | ✅ | UUID of the event |
| `reminder_days` | ✅ | The reminder (in days) to remove |

---

## Automation Triggers

The integration fires two HA bus events that can be used as automation triggers.

### `hebrew_calendar_event_today`

Fired at midnight when an event falls on today's Hebrew date.

```yaml
trigger:
  - platform: event
    event_type: hebrew_calendar_event_today
```

**Event data:**

```yaml
event_id: "..."
event_name: "Yossi's Birthday"
event_type: "יום הולדת"
hebrew_date: "15/1/5785"
gregorian_date: "2024-10-17"
is_recurring: true
```

---

### `hebrew_calendar_reminder_today`

Fired at midnight when a reminder is due (N days before an event).

```yaml
trigger:
  - platform: event
    event_type: hebrew_calendar_reminder_today
```

**Event data:**

```yaml
event_id: "..."
event_name: "Yossi's Birthday"
event_type: "יום הולדת"
days_until_event: 7
event_hebrew_date: "15/1/5785"
event_gregorian_date: "2024-10-17"
reminder_days: 7
```

---

## Automation Examples

### Notify when reminders are due today

This automation runs at midnight, checks whether `sensor.hebrew_calendar_reminders_today` has any events (using the `has_events` attribute), and if so sends a notification listing each event name and how many days away it is.

```yaml
alias: Hebrew Calendar - Daily Reminder Notification
description: Sends a notification each morning for any Hebrew calendar reminders due today.
trigger:
  - platform: time
    at: "07:00:00"
condition:
  - condition: template
    value_template: "{{ state_attr('sensor.hebrew_calendar_reminders_today', 'has_events') }}"
action:
  - service: notify.notify
    data:
      title: "📅 Hebrew Calendar Reminders"
      message: "{{ state_attr('sensor.hebrew_calendar_reminders_today', 'summary') }}"
mode: single
```

> **Tip:** Replace `notify.notify` with your preferred notification service, e.g. `notify.mobile_app_my_phone` or `notify.telegram`.

---

## Lovelace Card

A custom card (`hebrew-calendar-card.js`) is included to display your events in a Lovelace dashboard.

### Adding the card resource

Add the following to your dashboard resources (Settings → Dashboards → Resources):

```yaml
url: /local/hebrew-calendar-card.js
type: module
```

### Card configuration

```yaml
type: custom:hebrew-calendar-card
entity: sensor.hebrew_calendar_events
```

---

## Hebrew Months Reference

| # | Hebrew | Transliteration |
|---|--------|----------------|
| 1 | ניסן | Nisan |
| 2 | אייר | Iyar |
| 3 | סיון | Sivan |
| 4 | תמוז | Tammuz |
| 5 | אב | Av |
| 6 | אלול | Elul |
| 7 | תשרי | Tishrei |
| 8 | חשון | Cheshvan |
| 9 | כסלו | Kislev |
| 10 | טבת | Tevet |
| 11 | שבט | Shevat |
| 12 | אדר | Adar |
| 13 | אדר ב׳ | Adar II *(leap years only)* |

---

## Requirements

- Home Assistant **2023.1.0** or newer
- Python package: [`pyluach>=1.3.0`](https://pypi.org/project/pyluach/) — installed automatically

---

## Troubleshooting

**Events not firing at midnight**
Make sure your HA timezone is configured correctly in Settings → System → General.

**Date conversion errors**
The integration requires `pyluach`. If it fails to install, run `pip install pyluach` in your HA environment and restart.

**Sensor not updating after adding an event**
The sensors update in real time via HA bus events. If they appear stale, trigger a manual refresh from Developer Tools → Template.

---

## Contributing

Pull requests are welcome! Please open an issue first to discuss any significant changes.

---

## License

MIT License — see [LICENSE](LICENSE) for details.