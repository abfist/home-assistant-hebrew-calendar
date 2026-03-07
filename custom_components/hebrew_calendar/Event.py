import logging
from typing import List
from .HebrewDateConverter import HebrewDateConverter
from datetime import date
_LOGGER = logging.getLogger(__name__)

class Event:
  id: str
  event_name: str
  event_type: str
  hebrew_day: int
  hebrew_month: int
  hebrew_year: int|None
  is_recurring: bool
  reminders: list[int]
#   gregorian_date: str
#   days_until: int
#   hebrew_date_string:str
  @property
  def original_gregorian_date(self):
    gregorianDate=self.getOriginalGregorianDate()
    return str(gregorianDate) if gregorianDate else None
  

  @property
  def gregorian_date(self):
    gregorianDate=self.getGregorianDate()
    return str(gregorianDate) if gregorianDate else None
  
  @classmethod
  def fromDict(cls, data: dict) -> "Event":
      obj = cls()
      obj.id = data.get("id", "")
      obj.event_name = data.get("event_name", "")
      obj.event_type = data.get("event_type", "")
      obj.hebrew_day = data.get("hebrew_day", 0)
      obj.hebrew_month = data.get("hebrew_month", 0)
      obj.hebrew_year = data.get("hebrew_year", None)
      obj.is_recurring = data.get("is_recurring", True)
      obj.reminders = data.get("reminders", []).copy()
      return obj

  @classmethod
  def fromEvent(cls, event: "Event") -> "Event":
    obj = cls()
    obj.id = event.id
    obj.event_name = event.event_name
    obj.event_type = event.event_type
    obj.hebrew_day = event.hebrew_day
    obj.hebrew_month = event.hebrew_month
    obj.hebrew_year = event.hebrew_year
    obj.is_recurring = event.is_recurring
    obj.reminders = event.reminders.copy()
    return obj
  
  @staticmethod
  def fromEventList(eventList: List["Event"]) -> List["Event"]:
    copyOfList:List["Event"]=[]
    for event in eventList:
      copyOfList.append(Event.fromEvent(event))
    return copyOfList
   
  def getGregorianDate(self):
    try:
      year = self._getHebrewYear()
      # אם החודש לא קיים בשנה זו (למשל אדר ב׳ בשנה רגילה), דלג
      if not HebrewDateConverter.isValidHebrewMonthInYear(self.hebrew_month, year):
          _LOGGER.debug(
              "Month %d does not exist in Hebrew year %d for event %s, skipping",
              self.hebrew_month, year, self.id,
          )
          return None
      # אם היום גדול ממספר ימי החודש, השתמש ביום האחרון
      actual_day = HebrewDateConverter.getValidDay(self.hebrew_day, self.hebrew_month, year)
      if actual_day != self.hebrew_day:
          _LOGGER.debug(
              "Day %d clamped to %d for month %d year %d (event %s)",
              self.hebrew_day, actual_day, self.hebrew_month, year, self.id,
          )
      return HebrewDateConverter.hebrewToGregorian(actual_day, self.hebrew_month, year)
    except Exception as e:
        _LOGGER.debug("Could not get gregorian date for event %s: %s", self.id, e)
        return None
    
  def getOriginalGregorianDate(self):
    try:
      if self.hebrew_year is None:
        year = HebrewDateConverter.getCurrentHebrewYear()
      else:
        year = self.hebrew_year
      if not HebrewDateConverter.isValidHebrewMonthInYear(self.hebrew_month, year):
          return None
      actual_day = HebrewDateConverter.getValidDay(self.hebrew_day, self.hebrew_month, year)
      return HebrewDateConverter.hebrewToGregorian(actual_day, self.hebrew_month, year)
    except Exception as e:
        _LOGGER.debug("Could not get gregorian date for event %s: %s", self.id, e)
        return None
    

  @property
  def days_until(self):
    gregorianDate=self.getGregorianDate()
    return (gregorianDate - date.today()).days if gregorianDate else None
  
  @property
  def hebrew_date_string(self):
    return HebrewDateConverter.hebrewDateToString(
        self.hebrew_day,
        self.hebrew_month,
        self._getHebrewYear(),
    )
  

  def _getHebrewYear(self):
    '''מחזיר את השנה לחישובים השונים מתחשב באם זה ארוע חוזר או ארוע יחיד.
    עבור אירועים חוזרים שתאריכם כבר עבר השנה, מחזיר את השנה הבאה.
    אם החודש לא קיים בשנה הנוכחית (למשל אדר ב׳ בשנה רגילה), מחפש את השנה הבאה שבה קיים.'''
    if self.is_recurring or not self.hebrew_year:
      year = HebrewDateConverter.getCurrentHebrewYear()
      # חיפוש השנה הקרובה שבה החודש קיים (רלוונטי לאדר ב׳)
      for _ in range(20):  # מקסימום 20 שנה קדימה
          if HebrewDateConverter.isValidHebrewMonthInYear(self.hebrew_month, year):
              break
          year += 1
      else:
          return year  # לא נמצא — החזר כפי שהוא
      # אם התאריך כבר עבר השנה, נשתמש בשנה הבאה שבה החודש קיים
      try:
        actual_day = HebrewDateConverter.getValidDay(self.hebrew_day, self.hebrew_month, year)
        candidate = HebrewDateConverter.hebrewToGregorian(actual_day, self.hebrew_month, year)
        if candidate is not None and candidate < date.today():
          year += 1
          # ודא שהחודש קיים גם בשנה הבאה
          for _ in range(20):
              if HebrewDateConverter.isValidHebrewMonthInYear(self.hebrew_month, year):
                  break
              year += 1
      except Exception:
        pass
    else:
      year = self.hebrew_year
    return year

  def isToday(self):
    if self.days_until==0:
      return True
    
  def isReminderToday(self):
    if self.days_until in self.reminders:
      return True
    
  def as_dict(self) -> dict:
    year = self._getHebrewYear()
    # חישוב היום בפועל (לאחר clamping אם צריך)
    actual_day = self.hebrew_day
    date_note = None
    if HebrewDateConverter.isValidHebrewMonthInYear(self.hebrew_month, year):
        clamped = HebrewDateConverter.getValidDay(self.hebrew_day, self.hebrew_month, year)
        if clamped != self.hebrew_day:
            actual_day = clamped
            last_day_name = HebrewDateConverter.hebrewDateToString(clamped, self.hebrew_month, year)
            date_note = f"יום {self.hebrew_day} אינו קיים בחודש זה בשנה זו — מוצג כ-{last_day_name}"
    return {
        "id": self.id,
        "event_name": self.event_name,
        "event_type": self.event_type,
        "hebrew_day": actual_day,
        "hebrew_month": self.hebrew_month,
        "hebrew_year": self.hebrew_year,
        "is_recurring": self.is_recurring,
        "reminders": self.reminders.copy(),
        "hebrew_date_string": self.hebrew_date_string,
        "gregorian_date": self.gregorian_date,
        "days_until": self.days_until,
        "date_note": date_note,  # הערה אם היום נוצר בצורה מעוגלת
    }  
        # enriched_events = []
        # for event in self._events:
        #     year = today_hebrew["year"] if event.get(ATTR_IS_RECURRING) else event.get(ATTR_HEBREW_YEAR)
        #     gregorian = self._get_event_gregorian_date(event, year)
            
        #     enriched = {
        #         **event,
        #         "hebrew_date_string": self._converter.hebrew_date_to_string(
        #             event[ATTR_HEBREW_DAY],
        #             event[ATTR_HEBREW_MONTH],
        #             year,
        #         ),
        #         "gregorian_date": str(gregorian) if gregorian else None,
        #         "days_until": (gregorian - date.today()).days if gregorian else None,
        #     }