/**
 * Hebrew Calendar Card - Lovelace Custom Card
 * =============================================
 * כרטיס Lovelace לניהול אירועים בלוח שנה עברי.
 * 
 * תכונות:
 * - הצגת רשימת כל האירועים
 * - הוספה, עריכה ומחיקה של אירועים
 * - ניהול תזכורות לכל אירוע
 * - תצוגה בעברית עם RTL
 * 
 * שימוש ב-Lovelace:
 * type: custom:hebrew-calendar-card
 * entity: sensor.hebrew_calendar_events
 */

const HEBREW_MONTHS = {
  1: 'תשרי', 2: 'חשון', 3: 'כסלו', 4: 'טבת', 5: 'שבט',
  6: 'אדר', 7: 'ניסן', 8: 'אייר', 9: 'סיון', 10: 'תמוז',
  11: 'אב', 12: 'אלול', 13: 'אדר א׳'
};

const EVENT_TYPES = ['יום הולדת', 'יארצייט', 'יום נישואין', 'חג', 'אחר'];

const DOMAIN = 'hebrew_calendar';

/**
 * הכרטיס הראשי - Hebrew Calendar Card
 * מנהל את כל הלוגיקה וה-UI של הכרטיס.
 */
class HebrewCalendarCard extends HTMLElement {
  
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._hass = null;
    this._config = null;
    this._events = [];
    this._editingEvent = null; // null = טופס הוספה, object = עריכה
    this._showForm = false;
    this._currentReminders = []; // תזכורות בטופס הפעיל
  }

  /**
   * הגדרת קונפיגורציה של הכרטיס מ-YAML.
   * @param {Object} config - קונפיגורציה מ-Lovelace
   */
  setConfig(config) {
    if (!config.entity) {
      throw new Error('חובה להגדיר entity (sensor.hebrew_calendar_events)');
    }
    this._config = config;
    this.render();
  }

  /**
   * קבלת hass object ועדכון המצב.
   * נקרא בכל פעם שמשהו ב-HA משתנה.
   */
  set hass(hass) {
    this._hass = hass;
    
    // קבלת נתוני האירועים מה-sensor
    const stateObj = hass.states[this._config.entity];
    if (stateObj && stateObj.attributes.events) {
      this._events = stateObj.attributes.events;
    }
    
    this.render();
  }

  /**
   * ערך הגובה הרצוי של הכרטיס.
   * @returns {number} - גובה ב-units
   */
  getCardSize() {
    return Math.max(3, Math.ceil(this._events.length / 2) + 2);
  }

  /**
   * קריאה לשירות HA.
   * @param {string} service - שם השירות
   * @param {Object} data - נתונים לשירות
   */
  async _callService(service, data) {
    await this._hass.callService(DOMAIN, service, data);
  }

  /**
   * פתיחת טופס הוספת אירוע חדש.
   */
  _openAddForm() {
    this._editingEvent = null;
    this._showForm = true;
    this._currentReminders = [];
    this.render();
    this._focusFirstInput();
  }

  /**
   * פתיחת טופס עריכת אירוע קיים.
   * @param {Object} event - נתוני האירוע לעריכה
   */
  _openEditForm(event) {
    this._editingEvent = event;
    this._showForm = true;
    this._currentReminders = [...(event.reminders || [])];
    this.render();
    this._prefillForm(event);
  }

  /**
   * סגירת הטופס וחזרה לתצוגה הראשית.
   */
  _closeForm() {
    this._showForm = false;
    this._editingEvent = null;
    this._currentReminders = [];
    this.render();
  }

  /**
   * מילוי הטופס בנתוני אירוע קיים (לעריכה).
   * @param {Object} event - נתוני האירוע
   */
  _prefillForm(event) {
    setTimeout(() => {
      const root = this.shadowRoot;
      if (!root) return;
      
      const setValue = (id, value) => {
        const el = root.getElementById(id);
        if (el && value !== undefined && value !== null) el.value = value;
      };
      
      setValue('event-name', event.event_name);
      setValue('event-type', event.event_type);
      setValue('hebrew-day', event.hebrew_day);
      setValue('hebrew-month', event.hebrew_month);
      setValue('hebrew-year', event.hebrew_year || '');
      
      const recurringEl = root.getElementById('is-recurring');
      if (recurringEl) recurringEl.checked = event.is_recurring !== false;
    }, 50);
  }

  /**
   * שמירת אירוע (הוספה או עריכה).
   * אוסף את כל הנתונים מהטופס וקורא לשירות המתאים.
   */
  async _saveEvent() {
    const root = this.shadowRoot;
    
    const getValue = (id) => root.getElementById(id)?.value;
    const getChecked = (id) => root.getElementById(id)?.checked;
    
    const name = getValue('event-name');
    const type = getValue('event-type');
    const day = parseInt(getValue('hebrew-day'));
    const month = parseInt(getValue('hebrew-month'));
    const yearVal = getValue('hebrew-year');
    const year = yearVal ? parseInt(yearVal) : null;
    const isRecurring = getChecked('is-recurring') !== false;
    
    // ולידציה בסיסית
    if (!name || !type || !day || !month) {
      this._showError('יש למלא את כל השדות החובה');
      return;
    }
    
    const data = {
      event_name: name,
      event_type: type,
      hebrew_day: day,
      hebrew_month: month,
      is_recurring: isRecurring,
      reminders: this._currentReminders,
    };
    
    if (year) data.hebrew_year = year;
    if (!isRecurring && !year) {
      this._showError('אירוע חד-פעמי חייב שנה עברית');
      return;
    }
    
    try {
      if (this._editingEvent) {
        await this._callService('edit_event', {
          event_id: this._editingEvent.id,
          ...data,
        });
      } else {
        await this._callService('add_event', data);
      }
      this._closeForm();
    } catch (e) {
      this._showError('שגיאה בשמירת האירוע: ' + e.message);
    }
  }

  /**
   * מחיקת אירוע לאחר אישור.
   * @param {string} eventId - מזהה האירוע
   * @param {string} eventName - שם האירוע (לאישור)
   */
  async _deleteEvent(eventId, eventName) {
    if (!confirm(`האם למחוק את "${eventName}"?`)) return;
    
    try {
      await this._callService('remove_event', { event_id: eventId });
    } catch (e) {
      this._showError('שגיאה במחיקת האירוע');
    }
  }

  /**
   * הוספת תזכורת לרשימת התזכורות בטופס.
   */
  _addReminder() {
    const root = this.shadowRoot;
    const input = root.getElementById('reminder-input');
    const days = parseInt(input?.value);
    
    if (isNaN(days) || days < 0) {
      this._showError('יש להזין מספר ימים תקין');
      return;
    }
    
    if (this._currentReminders.includes(days)) {
      this._showError('תזכורת זו כבר קיימת');
      return;
    }
    
    this._currentReminders = [...this._currentReminders, days].sort((a, b) => a - b);
    if (input) input.value = '';
    this._updateRemindersList();
  }

  /**
   * הסרת תזכורת מהרשימה בטופס.
   * @param {number} days - מספר הימים של התזכורת
   */
  _removeReminder(days) {
    this._currentReminders = this._currentReminders.filter(d => d !== days);
    this._updateRemindersList();
  }

  /**
   * עדכון תצוגת רשימת התזכורות בטופס (ללא re-render מלא).
   */
  _updateRemindersList() {
    const container = this.shadowRoot.getElementById('reminders-list');
    if (container) {
      container.innerHTML = this._renderRemindersList();
      this._attachReminderListeners();
    }
  }

  /**
   * הצגת הודעת שגיאה זמנית.
   * @param {string} message - הודעת השגיאה
   */
  _showError(message) {
    const errorEl = this.shadowRoot.getElementById('form-error');
    if (errorEl) {
      errorEl.textContent = message;
      errorEl.style.display = 'block';
      setTimeout(() => { errorEl.style.display = 'none'; }, 3000);
    }
  }

  /**
   * פוקוס על השדה הראשון בטופס.
   */
  _focusFirstInput() {
    setTimeout(() => {
      const input = this.shadowRoot.getElementById('event-name');
      if (input) input.focus();
    }, 100);
  }

  // ============================================================
  // ייצור HTML
  // ============================================================

  /**
   * ייצור CSS סגנון הכרטיס.
   * @returns {string} CSS
   */
  _getStyles() {
    return `
      :host {
        direction: rtl;
        font-family: var(--paper-font-body1_-_font-family);
      }
      ha-card {
        padding: 16px;
      }
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
      }
      .card-title {
        font-size: 1.2em;
        font-weight: bold;
        color: var(--primary-text-color);
      }
      .add-btn {
        background: var(--primary-color);
        color: white;
        border: none;
        border-radius: 50%;
        width: 36px;
        height: 36px;
        font-size: 20px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .event-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      .event-card {
        background: var(--card-background-color);
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        padding: 12px;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
      }
      .event-info {
        flex: 1;
      }
      .event-name {
        font-weight: bold;
        font-size: 1em;
        color: var(--primary-text-color);
      }
      .event-type {
        font-size: 0.8em;
        color: var(--secondary-text-color);
        margin-top: 2px;
      }
      .event-date {
        font-size: 0.85em;
        color: var(--primary-color);
        margin-top: 4px;
      }
      .event-days-until {
        font-size: 0.8em;
        color: var(--success-color, green);
        margin-top: 2px;
      }
      .event-reminders {
        font-size: 0.75em;
        color: var(--secondary-text-color);
        margin-top: 4px;
      }
      .event-actions {
        display: flex;
        gap: 4px;
      }
      .icon-btn {
        background: none;
        border: none;
        cursor: pointer;
        padding: 4px;
        border-radius: 4px;
        font-size: 16px;
        color: var(--secondary-text-color);
      }
      .icon-btn:hover { background: var(--secondary-background-color); }
      .icon-btn.delete:hover { color: var(--error-color); }
      .badge {
        display: inline-block;
        background: var(--primary-color);
        color: white;
        border-radius: 12px;
        padding: 1px 8px;
        font-size: 0.75em;
        margin-top: 4px;
      }
      .badge.recurring { background: var(--info-color, #2196f3); }
      .badge.once { background: var(--warning-color, #ff9800); }
      /* ======= טופס ======= */
      .form-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,0.5);
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 16px;
      }
      .form-container {
        background: var(--card-background-color);
        border-radius: 12px;
        padding: 20px;
        width: 100%;
        max-width: 480px;
        max-height: 90vh;
        overflow-y: auto;
        direction: rtl;
      }
      .form-title {
        font-size: 1.1em;
        font-weight: bold;
        margin-bottom: 16px;
        color: var(--primary-text-color);
      }
      .form-row {
        margin-bottom: 14px;
      }
      .form-row label {
        display: block;
        font-size: 0.85em;
        color: var(--secondary-text-color);
        margin-bottom: 4px;
      }
      .form-row input, .form-row select {
        width: 100%;
        padding: 8px 10px;
        border: 1px solid var(--divider-color);
        border-radius: 6px;
        font-size: 0.95em;
        background: var(--card-background-color);
        color: var(--primary-text-color);
        box-sizing: border-box;
        direction: rtl;
      }
      .form-row input:focus, .form-row select:focus {
        outline: none;
        border-color: var(--primary-color);
      }
      .checkbox-row {
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .checkbox-row input { width: auto; }
      .reminder-input-row {
        display: flex;
        gap: 8px;
        align-items: flex-end;
      }
      .reminder-input-row .form-row { flex: 1; margin: 0; }
      .reminder-add-btn {
        background: var(--primary-color);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 14px;
        cursor: pointer;
        white-space: nowrap;
      }
      .reminders-list {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-top: 8px;
        min-height: 28px;
      }
      .reminder-tag {
        background: var(--secondary-background-color);
        border-radius: 16px;
        padding: 3px 10px 3px 6px;
        font-size: 0.85em;
        display: flex;
        align-items: center;
        gap: 4px;
      }
      .reminder-tag button {
        background: none;
        border: none;
        cursor: pointer;
        color: var(--secondary-text-color);
        font-size: 14px;
        padding: 0;
        line-height: 1;
      }
      .form-actions {
        display: flex;
        gap: 8px;
        justify-content: flex-end;
        margin-top: 20px;
      }
      .btn-save {
        background: var(--primary-color);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 20px;
        cursor: pointer;
        font-size: 0.95em;
      }
      .btn-cancel {
        background: transparent;
        color: var(--secondary-text-color);
        border: 1px solid var(--divider-color);
        border-radius: 6px;
        padding: 8px 20px;
        cursor: pointer;
        font-size: 0.95em;
      }
      .error-msg {
        color: var(--error-color);
        font-size: 0.85em;
        padding: 6px;
        background: rgba(255,0,0,0.1);
        border-radius: 4px;
        margin-top: 8px;
        display: none;
      }
      .empty-state {
        text-align: center;
        color: var(--secondary-text-color);
        padding: 24px;
      }
      .empty-state .icon { font-size: 2em; margin-bottom: 8px; }
    `;
  }

  /**
   * ייצור HTML של רשימת תזכורות בטופס.
   * @returns {string} HTML
   */
  _renderRemindersList() {
    if (this._currentReminders.length === 0) {
      return '<span style="color:var(--secondary-text-color);font-size:0.8em">אין תזכורות</span>';
    }
    return this._currentReminders.map(d =>
      `<span class="reminder-tag">
        ${d === 0 ? 'ביום האירוע' : `${d} ימים לפני`}
        <button data-remove="${d}" title="הסר">✕</button>
      </span>`
    ).join('');
  }

  /**
   * ייצור HTML של כרטיסי האירועים.
   * @returns {string} HTML
   */
  _renderEventList() {
    if (this._events.length === 0) {
      return `
        <div class="empty-state">
          <div class="icon">📅</div>
          <div>אין אירועים עדיין</div>
          <div style="font-size:0.85em;margin-top:4px">לחץ על + להוספת אירוע ראשון</div>
        </div>`;
    }

    return this._events.map(event => {
      const remindersText = event.reminders && event.reminders.length > 0
        ? '🔔 ' + event.reminders.map(d => d === 0 ? 'ביום האירוע' : `${d} ימים לפני`).join(' | ')
        : '';
      
      const daysUntil = event.days_until;
      let daysText = '';
      if (daysUntil === 0) daysText = '🎉 היום!';
      else if (daysUntil === 1) daysText = 'מחר';
      else if (daysUntil > 0 && daysUntil <= 30) daysText = `בעוד ${daysUntil} ימים`;
      
      return `
        <div class="event-card">
          <div class="event-info">
            <div class="event-name">${event.event_name}</div>
            <div class="event-type">${event.event_type}</div>
            <div class="event-date">📅 ${event.hebrew_date_string || ''}</div>
            ${daysText ? `<div class="event-days-until">${daysText}</div>` : ''}
            ${remindersText ? `<div class="event-reminders">${remindersText}</div>` : ''}
            <span class="badge ${event.is_recurring ? 'recurring' : 'once'}">
              ${event.is_recurring ? '↻ חוזר' : '· חד-פעמי'}
            </span>
          </div>
          <div class="event-actions">
            <button class="icon-btn" data-edit='${JSON.stringify(event).replace(/'/g, "&#39;")}' title="ערוך">✏️</button>
            <button class="icon-btn delete" data-delete="${event.id}" data-name="${event.event_name}" title="מחק">🗑️</button>
          </div>
        </div>`;
    }).join('');
  }

  /**
   * ייצור HTML של הטופס (הוספה/עריכה).
   * @returns {string} HTML
   */
  _renderForm() {
    const isEdit = !!this._editingEvent;
    const title = isEdit ? `עריכת: ${this._editingEvent.event_name}` : 'הוספת אירוע חדש';
    
    const monthOptions = Object.entries(HEBREW_MONTHS)
      .map(([num, name]) => `<option value="${num}">${name}</option>`)
      .join('');
    
    const typeOptions = EVENT_TYPES
      .map(t => `<option value="${t}">${t}</option>`)
      .join('');
    
    return `
      <div class="form-overlay" id="form-overlay">
        <div class="form-container">
          <div class="form-title">${title}</div>
          
          <div class="form-row">
            <label>שם האירוע *</label>
            <input id="event-name" type="text" placeholder="לדוגמה: יום הולדת יוסי" />
          </div>
          
          <div class="form-row">
            <label>סוג האירוע *</label>
            <select id="event-type">${typeOptions}</select>
          </div>
          
          <div style="display:flex;gap:8px">
            <div class="form-row" style="flex:1">
              <label>יום *</label>
              <input id="hebrew-day" type="number" min="1" max="30" placeholder="1-30" />
            </div>
            <div class="form-row" style="flex:2">
              <label>חודש *</label>
              <select id="hebrew-month">${monthOptions}</select>
            </div>
          </div>
          
          <div class="form-row">
            <div class="checkbox-row">
              <input id="is-recurring" type="checkbox" checked />
              <label for="is-recurring" style="display:inline">אירוע חוזר מדי שנה</label>
            </div>
          </div>
          
          <div class="form-row">
            <label>שנה עברית (לאירועים חד-פעמיים)</label>
            <input id="hebrew-year" type="number" min="5700" max="6000" placeholder="לדוגמה: 5784" />
          </div>
          
          <div class="form-row">
            <label>תזכורות</label>
            <div class="reminder-input-row">
              <div class="form-row">
                <input id="reminder-input" type="number" min="0" max="365" placeholder="ימים לפני האירוע" />
              </div>
              <button class="reminder-add-btn" id="add-reminder-btn">הוסף</button>
            </div>
            <div class="reminders-list" id="reminders-list">
              ${this._renderRemindersList()}
            </div>
          </div>
          
          <div class="error-msg" id="form-error"></div>
          
          <div class="form-actions">
            <button class="btn-cancel" id="cancel-btn">ביטול</button>
            <button class="btn-save" id="save-btn">שמור</button>
          </div>
        </div>
      </div>`;
  }

  /**
   * רינדור מלא של הכרטיס.
   * מייצר את כל ה-HTML ומצרף event listeners.
   */
  render() {
    const title = this._config?.title || 'לוח שנה עברי';
    const currentDate = this._hass?.states[this._config?.entity]?.attributes?.current_hebrew_date || '';
    
    this.shadowRoot.innerHTML = `
      <style>${this._getStyles()}</style>
      <ha-card>
        <div class="card-header">
          <div>
            <div class="card-title">📅 ${title}</div>
            ${currentDate ? `<div style="font-size:0.8em;color:var(--secondary-text-color)">${currentDate}</div>` : ''}
          </div>
          <button class="add-btn" id="add-btn" title="הוסף אירוע">+</button>
        </div>
        <div class="event-list">
          ${this._renderEventList()}
        </div>
        ${this._showForm ? this._renderForm() : ''}
      </ha-card>`;
    
    this._attachEventListeners();
  }

  /**
   * צירוף כל event listeners לאחר render.
   */
  _attachEventListeners() {
    const root = this.shadowRoot;
    
    // כפתור הוספה
    root.getElementById('add-btn')?.addEventListener('click', () => this._openAddForm());
    
    // כפתורי עריכה
    root.querySelectorAll('[data-edit]').forEach(btn => {
      btn.addEventListener('click', () => {
        try {
          const event = JSON.parse(btn.getAttribute('data-edit'));
          this._openEditForm(event);
        } catch(e) { console.error('Parse error', e); }
      });
    });
    
    // כפתורי מחיקה
    root.querySelectorAll('[data-delete]').forEach(btn => {
      btn.addEventListener('click', () => {
        this._deleteEvent(btn.getAttribute('data-delete'), btn.getAttribute('data-name'));
      });
    });
    
    // כפתורי טופס
    root.getElementById('save-btn')?.addEventListener('click', () => this._saveEvent());
    root.getElementById('cancel-btn')?.addEventListener('click', () => this._closeForm());
    
    // סגירה בלחיצה על ה-overlay
    root.getElementById('form-overlay')?.addEventListener('click', (e) => {
      if (e.target.id === 'form-overlay') this._closeForm();
    });
    
    // כפתור הוספת תזכורת
    root.getElementById('add-reminder-btn')?.addEventListener('click', () => this._addReminder());
    
    // Enter בשדה תזכורת
    root.getElementById('reminder-input')?.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') this._addReminder();
    });
    
    // כפתורי הסרת תזכורות
    this._attachReminderListeners();
  }

  /**
   * צירוף listeners לכפתורי הסרת תזכורות.
   */
  _attachReminderListeners() {
    this.shadowRoot.querySelectorAll('[data-remove]').forEach(btn => {
      btn.addEventListener('click', () => {
        this._removeReminder(parseInt(btn.getAttribute('data-remove')));
      });
    });
  }
}

// רישום הכרטיס ב-Custom Elements
customElements.define('hebrew-calendar-card', HebrewCalendarCard);

// מידע עבור Lovelace card picker
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'hebrew-calendar-card',
  name: 'Hebrew Calendar Card',
  description: 'כרטיס לניהול אירועים בלוח שנה עברי',
  preview: false,
});

console.info(
  '%c HEBREW-CALENDAR-CARD %c v1.0.0 ',
  'color: white; background: #3b5998; font-weight: bold;',
  'color: #3b5998; background: white; font-weight: bold;'
);
