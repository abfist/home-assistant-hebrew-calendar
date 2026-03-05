/**
 * Hebrew Calendar Card - Lovelace Custom Card
 * =============================================
 * הטופס רץ כ-dialog נפרד על ה-body — מחוץ ל-Shadow DOM —
 * כך שרענון הכרטיס לא משפיע עליו כלל.
 */

const HEBREW_MONTHS = {
  7: 'תשרי', 8: 'חשון', 9: 'כסלו', 10: 'טבת', 11: 'שבט',
  13: 'אדר ב׳', 12: 'אדר', 1: 'ניסן', 2: 'אייר', 3: 'סיון',
  4: 'תמוז', 5: 'אב', 6: 'אלול'
};

function getMonthName(month, year) {
  return HEBREW_MONTHS[month] || String(month);
}

// function getMonthName(month, year) {
//   const isLeap = year ? ((7 * year + 1) % 19 < 7) : true;
//   const map = isLeap ? HEBREW_MONTHS_LEAP : HEBREW_MONTHS_REGULAR;
//   return map[month] || String(month);
// }

const EVENT_TYPES = ['יום הולדת', 'יארצייט', 'יום נישואין', 'חג', 'אחר'];
const DOMAIN = 'hebrew_calendar';

/* ============================================================
   HebrewCalendarDialog — טופס הוספה/עריכה כ-element נפרד על ה-body
   כך שרענון הכרטיס לא נוגע בו כלל
   ============================================================ */
class HebrewCalendarDialog extends HTMLElement {
  constructor() {
    super();
    this._hass = null;
    this._editingEvent = null;
    this._reminders = [];
    this._onClose = null; // callback לסגירה
  }

  /** פתיחת הדיאלוג */
  open(hass, editingEvent, onClose) {
    this._hass = hass;
    this._editingEvent = editingEvent || null;
    this._reminders = editingEvent ? [...(editingEvent.reminders || [])] : [];
    this._onClose = onClose;
    document.body.appendChild(this);
    this._render();
  }

  /** סגירת הדיאלוג */
  close() {
    if (this._onClose) this._onClose();
    if (this.parentNode) this.parentNode.removeChild(this);
  }

  /** קריאה לשירות HA */
  async _callService(service, data) {
    await this._hass.callService(DOMAIN, service, data);
  }

  /** שמירת האירוע */
  async _save() {
    const g = (id) => this.querySelector('#' + id);
    const name = g('hc-name')?.value?.trim();
    const type = g('hc-type')?.value;
    const day = parseInt(g('hc-day')?.value);
    const month = parseInt(g('hc-month')?.value);
    const yearV = g('hc-year')?.value;
    const year = yearV ? parseInt(yearV) : null;
    const recurring = g('hc-recurring')?.checked !== false;

    if (!name || !type || !day || !month) {
      g('hc-error').textContent = 'יש למלא את כל השדות החובה';
      g('hc-error').style.display = 'block';
      return;
    }
    if (!recurring && !year) {
      g('hc-error').textContent = 'אירוע חד-פעמי חייב שנה עברית';
      g('hc-error').style.display = 'block';
      return;
    }

    const data = {
      event_name: name, event_type: type, hebrew_day: day,
      hebrew_month: month, is_recurring: recurring,
      reminders: this._reminders
    };
    if (year) data.hebrew_year = year;

    try {
      if (this._editingEvent) {
        await this._callService('edit_event', { event_id: this._editingEvent.id, ...data });
      } else {
        await this._callService('add_event', data);
      }
      this.close();
    } catch (e) {
      g('hc-error').textContent = 'שגיאה: ' + e.message;
      g('hc-error').style.display = 'block';
    }
  }

  /** הוספת תזכורת */
  _addReminder() {
    const input = this.querySelector('#hc-reminder-input');
    const days = parseInt(input?.value);
    if (isNaN(days) || days < 0) return;
    if (this._reminders.includes(days)) return;
    this._reminders = [...this._reminders, days].sort((a, b) => a - b);
    input.value = '';
    this._updateRemindersList();
  }

  /** עדכון רשימת תזכורות בלי re-render מלא */
  _updateRemindersList() {
    const el = this.querySelector('#hc-reminders-list');
    if (el) el.innerHTML = this._remindersHTML();
    this._bindReminderRemove();
  }

  _remindersHTML() {
    if (!this._reminders.length)
      return '<span style="color:#888;font-size:.8em">אין תזכורות</span>';
    return this._reminders.map(d =>
      `<span class="hc-tag">${d === 0 ? 'ביום האירוע' : d + ' ימים לפני'}
        <button class="hc-tag-rm" data-days="${d}">✕</button>
      </span>`
    ).join('');
  }

  _bindReminderRemove() {
    this.querySelectorAll('.hc-tag-rm').forEach(btn => {
      btn.onclick = () => {
        this._reminders = this._reminders.filter(d => d !== parseInt(btn.dataset.days));
        this._updateRemindersList();
      };
    });
  }

  _render() {
    const ev = this._editingEvent;
    const title = ev ? `עריכת: ${ev.event_name}` : 'הוספת אירוע חדש';

    const MONTH_ORDER = [7, 8, 9, 10, 11, 12, 13, 1, 2, 3, 4, 5, 6];
    const monthOptions = MONTH_ORDER
      .map(key => `<option value="${key}">${HEBREW_MONTHS[key]}</option>`).join('');
    const typeOptions = EVENT_TYPES
      .map(t => `<option value="${t}">${t}</option>`).join('');

    this.innerHTML = `
      <style>
        .hc-overlay{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:9999;
          display:flex;align-items:center;justify-content:center;padding:16px}
        .hc-box{background:#fff;border-radius:12px;padding:20px;width:100%;max-width:460px;
          max-height:90vh;overflow-y:auto;direction:rtl;color:#111;font-family:sans-serif}
        .hc-title{font-size:1.1em;font-weight:bold;margin-bottom:16px}
        .hc-row{margin-bottom:12px}
        .hc-row label{display:block;font-size:.82em;color:#555;margin-bottom:3px}
        .hc-row input,.hc-row select{width:100%;padding:7px 10px;border:1px solid #ccc;
          border-radius:6px;font-size:.95em;box-sizing:border-box;direction:rtl;background:#fff}
        .hc-row input:focus,.hc-row select:focus{outline:none;border-color:#3b82f6}
        .hc-half{display:flex;gap:8px}
        .hc-half .hc-row{flex:1}
        .hc-check{display:flex;align-items:center;gap:8px;margin-bottom:12px}
        .hc-check input{width:auto}
        .hc-rem-row{display:flex;gap:8px;align-items:flex-end}
        .hc-rem-row .hc-row{flex:1;margin:0}
        .hc-add-btn{background:#3b82f6;color:#fff;border:none;border-radius:6px;
          padding:7px 14px;cursor:pointer;white-space:nowrap;font-size:.9em}
        #hc-reminders-list{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;min-height:26px}
        .hc-tag{background:#f0f0f0;border-radius:16px;padding:3px 8px 3px 6px;
          font-size:.82em;display:inline-flex;align-items:center;gap:4px}
        .hc-tag-rm{background:none;border:none;cursor:pointer;color:#888;font-size:13px;padding:0}
        #hc-error{color:red;font-size:.82em;background:#fff0f0;padding:6px;
          border-radius:4px;margin-top:8px;display:none}
        .hc-actions{display:flex;gap:8px;justify-content:flex-end;margin-top:18px}
        .hc-save{background:#3b82f6;color:#fff;border:none;border-radius:6px;
          padding:8px 22px;cursor:pointer;font-size:.95em}
        .hc-cancel{background:transparent;color:#555;border:1px solid #ccc;
          border-radius:6px;padding:8px 22px;cursor:pointer;font-size:.95em}
      </style>
      <div class="hc-overlay" id="hc-overlay">
        <div class="hc-box">
          <div class="hc-title">${title}</div>

          <div class="hc-row">
            <label>שם האירוע *</label>
            <input id="hc-name" type="text" placeholder="לדוגמה: יום הולדת יוסי"
              value="${ev ? ev.event_name : ''}">
          </div>

          <div class="hc-row">
            <label>סוג האירוע *</label>
            <select id="hc-type">${typeOptions}</select>
          </div>

          <div class="hc-half">
            <div class="hc-row">
              <label>יום *</label>
              <input id="hc-day" type="number" min="1" max="31" placeholder="1-31"
                value="${ev ? ev.hebrew_day : ''}">
            </div>
            <div class="hc-row">
              <label>חודש *</label>
              <select id="hc-month">${monthOptions}</select>
            </div>
          </div>

          <div class="hc-check">
            <input id="hc-recurring" type="checkbox" ${!ev || ev.is_recurring !== false ? 'checked' : ''}>
            <label for="hc-recurring">אירוע חוזר מדי שנה</label>
          </div>

          <div class="hc-row">
            <label>שנה עברית (לאירועים חד-פעמיים)</label>
            <input id="hc-year" type="number" min="5700" max="6000"
              placeholder="לדוגמה: 5785" value="${ev && ev.hebrew_year ? ev.hebrew_year : ''}">
          </div>

          <div class="hc-row">
            <label>תזכורות</label>
            <div class="hc-rem-row">
              <div class="hc-row">
                <input id="hc-reminder-input" type="number" min="0" max="365"
                  placeholder="ימים לפני האירוע">
              </div>
              <button class="hc-add-btn" id="hc-add-rem">הוסף</button>
            </div>
            <div id="hc-reminders-list">${this._remindersHTML()}</div>
          </div>

          <div id="hc-error"></div>

          <div class="hc-actions">
            <button class="hc-cancel" id="hc-cancel">ביטול</button>
            <button class="hc-save" id="hc-save">שמור</button>
          </div>
        </div>
      </div>`;

    // סגירה בלחיצה על overlay
    this.querySelector('#hc-overlay').onclick = (e) => {
      if (e.target.id === 'hc-overlay') this.close();
    };
    this.querySelector('#hc-cancel').onclick = () => this.close();
    this.querySelector('#hc-save').onclick = () => this._save();
    this.querySelector('#hc-add-rem').onclick = () => this._addReminder();
    this.querySelector('#hc-reminder-input').onkeypress = (e) => {
      if (e.key === 'Enter') this._addReminder();
    };
    this._bindReminderRemove();

    // מילוי שדות עריכה
    if (ev) {
      this.querySelector('#hc-type').value = ev.event_type;
      this.querySelector('#hc-month').value = ev.hebrew_month;
    }

    // פוקוס
    setTimeout(() => this.querySelector('#hc-name')?.focus(), 50);
  }
}

customElements.define('hebrew-calendar-dialog', HebrewCalendarDialog);


/* ============================================================
   HebrewCalendarCard — הכרטיס הראשי (רשימת אירועים בלבד)
   ============================================================ */
class HebrewCalendarCard extends HTMLElement {

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._hass = null;
    this._config = null;
    this._events = [];
  }

  setConfig(config) {
    if (!config.entity) throw new Error('חובה להגדיר entity');
    this._config = config;
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    const stateObj = hass.states[this._config.entity];
    if (stateObj?.attributes?.events) {
      this._events = stateObj.attributes.events;
    }
    this.render();
  }

  getCardSize() {
    return Math.max(3, this._events.length + 2);
  }

  /** פתיחת דיאלוג הוספה/עריכה */
  _openDialog(editingEvent) {
    const dialog = document.createElement('hebrew-calendar-dialog');
    dialog.open(this._hass, editingEvent || null, () => { });
  }

  /** מחיקת אירוע */
  async _deleteEvent(id, name) {
    if (!confirm(`האם למחוק את "${name}"?`)) return;
    await this._hass.callService(DOMAIN, 'remove_event', { event_id: id });
  }

  render() {
    const title = this._config?.title || 'לוח שנה עברי';
    const stateObj = this._hass?.states[this._config?.entity];
    const currentDate = stateObj?.attributes?.current_hebrew_date || '';

    this.shadowRoot.innerHTML = `
      <style>
        :host{direction:rtl}
        ha-card{padding:16px}
        .header{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
        .title{font-size:1.15em;font-weight:bold;color:var(--primary-text-color)}
        .sub{font-size:.78em;color:var(--secondary-text-color);margin-top:2px}
        .add-btn{background:var(--primary-color);color:#fff;border:none;border-radius:50%;
          width:36px;height:36px;font-size:20px;cursor:pointer;
          display:flex;align-items:center;justify-content:center;flex-shrink:0}
        .list{display:flex;flex-direction:column;gap:8px}
        .card{background:var(--card-background-color);border:1px solid var(--divider-color);
          border-radius:8px;padding:11px;display:flex;justify-content:space-between;align-items:flex-start}
        .name{font-weight:bold;color:var(--primary-text-color)}
        .type{font-size:.8em;color:var(--secondary-text-color);margin-top:2px}
        .date{font-size:.82em;color:var(--primary-color);margin-top:3px}
        .until{font-size:.78em;color:green;margin-top:2px}
        .rems{font-size:.75em;color:var(--secondary-text-color);margin-top:3px}
        .badge{display:inline-block;border-radius:12px;padding:1px 8px;
          font-size:.72em;margin-top:4px;color:#fff}
        .recurring{background:#2196f3}.once{background:#ff9800}
        .actions{display:flex;gap:4px;flex-shrink:0}
        .ibtn{background:none;border:none;cursor:pointer;padding:4px;
          border-radius:4px;font-size:15px;color:var(--secondary-text-color)}
        .ibtn:hover{background:var(--secondary-background-color)}
        .del:hover{color:var(--error-color)}
        .empty{text-align:center;color:var(--secondary-text-color);padding:24px}
        .empty .icon{font-size:2em;margin-bottom:8px}
      </style>
      <ha-card>
        <div class="header">
          <div>
            <div class="title">📅 ${title}</div>
            ${currentDate ? `<div class="sub">${currentDate}</div>` : ''}
          </div>
          <button class="add-btn" id="add-btn" title="הוסף אירוע">+</button>
        </div>
        <div class="list">${this._eventsHTML()}</div>
      </ha-card>`;

    this.shadowRoot.getElementById('add-btn').onclick = () => this._openDialog(null);

    this.shadowRoot.querySelectorAll('[data-edit]').forEach(btn => {
      btn.onclick = () => {
        try { this._openDialog(JSON.parse(btn.dataset.edit)); } catch (e) { }
      };
    });

    this.shadowRoot.querySelectorAll('[data-del]').forEach(btn => {
      btn.onclick = () => this._deleteEvent(btn.dataset.del, btn.dataset.name);
    });
  }

  _eventsHTML() {
    if (!this._events.length) return `
      <div class="empty">
        <div class="icon">📅</div>
        <div>אין אירועים עדיין</div>
        <div style="font-size:.82em;margin-top:4px">לחץ על + להוספה</div>
      </div>`;

    return this._events.map(ev => {
      const rems = (ev.reminders || []).filter(d => d > 0)
        .map(d => d + ' ימים לפני').join(' | ');
      const du = ev.days_until;
      const until = du === 0 ? '🎉 היום!' : du === 1 ? 'מחר' : du > 0 && du <= 30 ? `בעוד ${du} ימים` : '';
      const safeEv = JSON.stringify(ev).replace(/"/g, '&quot;');

      return `
        <div class="card">
          <div>
            <div class="name">${ev.event_name}</div>
            <div class="type">${ev.event_type}</div>
            <div class="date">📅 ${ev.hebrew_date_string || ''}</div>
            ${until ? `<div class="until">${until}</div>` : ''}
            ${rems ? `<div class="rems">🔔 ${rems}</div>` : ''}
            <span class="badge ${ev.is_recurring ? 'recurring' : 'once'}">
              ${ev.is_recurring ? '↻ חוזר' : '· חד-פעמי'}
            </span>
          </div>
          <div class="actions">
            <button class="ibtn" data-edit="${safeEv}" title="ערוך">✏️</button>
            <button class="ibtn del" data-del="${ev.id}" data-name="${ev.event_name}" title="מחק">🗑️</button>
          </div>
        </div>`;
    }).join('');
  }
}

customElements.define('hebrew-calendar-card', HebrewCalendarCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'hebrew-calendar-card',
  name: 'Hebrew Calendar Card',
  description: 'כרטיס לניהול אירועים בלוח שנה עברי',
});

console.info('%c HEBREW-CALENDAR-CARD %c v1.1.0 ',
  'color:white;background:#3b5998;font-weight:bold',
  'color:#3b5998;background:white;font-weight:bold');
