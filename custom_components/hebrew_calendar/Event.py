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
   
      return HebrewDateConverter.hebrewToGregorian(
          self["day"],
          self["month"],
          self._getHebrewYear(),
      )
    except Exception as e:
        _LOGGER.debug("Could not get gregorian date for event %s: %s", self.id, e)
        return None
    
  def getOriginalGregorianDate(self):
    try:
      if self.hebrew_year is None:
        year = HebrewDateConverter.getCurrentHebrewYear()
      else:
        year=self.hebrew_year
            
        return HebrewDateConverter.hebrewToGregorian(
            self["day"],
            self["month"],
            year,
        )
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
        self["day"],
        self["month"],
        self._getHebrewYear(),
    )
  

  def _getHebrewYear(self):
    '''מחזיר את השנה לחישובים השונים מתחשב באם זה ארוע חוזר או ארוע יחיד'''
    # fixMe: need to handle dates that passed so the next year will be handled for reminders
    if self.is_recurring or self.hebrew_year:
       year=HebrewDateConverter.getCurrentHebrewYear()
    else:
       year=self.hebrew_year
    return  year

  def isToday(self):
    if self.days_until==0:
      return True
    
  def isReminderToday(self):
    if self.days_until in self.reminders:
      return True
    
    
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
