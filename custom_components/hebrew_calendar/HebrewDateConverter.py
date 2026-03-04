import pyluach
import logging
from datetime import date
from typing import Dict, Optional

class HebrewDateConverter:
    """
    ממיר תאריכים בין לוח שנה עברי לגרגוריאני.
    
    שיטות עיקריות:
    - gregorian_to_hebrew: המרת תאריך גרגוריאני לעברי
    - hebrew_to_gregorian: המרת תאריך עברי לגרגוריאני
    - hebrew_date_to_string: המרת תאריך עברי למחרוזת קריאה
    """

    @staticmethod
    def gregorianToHebrew(gregorian_date: date) -> Dict[str, int]:
        """
        המרת תאריך גרגוריאני לתאריך עברי.
        
        Args:
            gregorian_date: תאריך גרגוריאני
            
        Returns:
            dict עם מפתחות: day, month, year
        """
        return HebrewDateConverter._pyluach_gregorian_to_hebrew(gregorian_date)
        
    @staticmethod
    def hebrewToGregorian(self, day: int, month: int, year: int) -> date:
        """
        המרת תאריך עברי לתאריך גרגוריאני.
        
        Args:
            day: יום בחודש העברי (1-31)
            month: חודש עברי (1-13)
            year: שנה עברית
            
        Returns:
            תאריך גרגוריאני מקביל
        """
        return HebrewDateConverter._pyluach_hebrew_to_gregorian(day, month, year)
        
    @staticmethod
    def getCurrentHebrewYear() -> int:
        """מחזיר את השנה העברית הנוכחית."""
        today = date.today()
        hebrewDate = HebrewDateConverter.gregorian_to_hebrew(today)
        return hebrewDate["year"]
    
    @staticmethod
    def getCurrentHebrewDay()->int:
        """מחזיר את היום העברי הנוכחי."""
        hebrewDate=HebrewDateConverter.gregorian_to_hebrew(date.today())
        return hebrewDate["day"]
    
    @staticmethod
    def getCurrentHebrewMonth()->int:
        """מחזיר את החודש העברי הנוכחי."""
        hebrewDate=HebrewDateConverter.gregorian_to_hebrew(date.today())
        return hebrewDate["month"]
    
    @staticmethod
    def getCurrentHebrewDate():
        """מחזיר את החודש העברי הנוכחי."""
        hebrewDate=HebrewDateConverter.gregorianToHebrew(date.today())
        return (hebrewDate["day"],hebrewDate["month"],hebrewDate["year"])


    @staticmethod
    def hebrewDateToString(day: int, month: int, year: Optional[int] = None) -> str:
        """
        המרת תאריך עברי למחרוזת קריאה בעברית.
        
        Args:
            day: יום
            month: חודש
            year: שנה (אופציונלי)
            
        Returns:
            מחרוזת כגון "ט״ו בתשרי תשפ״ה"
        """
        from .const import HEBREW_MONTHS
        
        month_name = HEBREW_MONTHS.get(month, str(month))
        day_str = HebrewDateConverter._number_to_hebrew_letters(day)
        
        if year:
            year_str = HebrewDateConverter._number_to_hebrew_letters(year % 1000)
            return f"{day_str} ב{month_name} {year_str}"
        else:
            return f"{day_str} ב{month_name}"
  
    @staticmethod
    def _number_to_hebrew_letters(num: int) -> str:
        """
        המרת מספר לאותיות עבריות (גימטריה).
        משמש לתצוגת תאריכים עבריים.
        """
        if num <= 0 or num > 9999:
            return str(num)
        
        letters = [
            (400, "ת"), (300, "ש"), (200, "ר"), (100, "ק"),
            (90, "צ"), (80, "פ"), (70, "ע"), (60, "ס"), (50, "נ"),
            (40, "מ"), (30, "ל"), (20, "כ"), (10, "י"),
            (9, "ט"), (8, "ח"), (7, "ז"), (6, "ו"), (5, "ה"),
            (4, "ד"), (3, "ג"), (2, "ב"), (1, "א"),
        ]
        
        # טיפול במקרים מיוחדים (15 ו-16)
        result = ""
        if num % 100 == 15:
            num -= 15
            result = "ט״ו"
        elif num % 100 == 16:
            num -= 16
            result = "ט״ז"
        
        parts = []
        for value, letter in letters:
            while num >= value:
                parts.append(letter)
                num -= value
        
        # הוספת גרשיים/גרש
        if parts:
            if len(parts) == 1:
                result = "".join(parts) + "׳" + result
            else:
                result = "".join(parts[:-1]) + "״" + parts[-1] + result
        
        return result
