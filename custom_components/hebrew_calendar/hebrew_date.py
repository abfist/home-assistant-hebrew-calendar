"""
Hebrew Date Converter
=====================
מודול להמרה בין תאריכים עבריים לגרגוריאניים.
משתמש בספריית pyluach לחישובים מדויקים.

אם pyluach אינה מותקנת, ישנה fallback לחישוב ידני מקורב.
"""

import logging
from datetime import date
from typing import Dict, Optional

_LOGGER = logging.getLogger(__name__)


class HebrewDateConverter:
    """
    ממיר תאריכים בין לוח שנה עברי לגרגוריאני.
    
    שיטות עיקריות:
    - gregorian_to_hebrew: המרת תאריך גרגוריאני לעברי
    - hebrew_to_gregorian: המרת תאריך עברי לגרגוריאני
    - hebrew_date_to_string: המרת תאריך עברי למחרוזת קריאה
    """

    def __init__(self):
        """אתחול הממיר ובדיקת זמינות ספריית pyluach."""
        self._pyluach_available = self._check_pyluach()

    def _check_pyluach(self) -> bool:
        """בדיקה אם ספריית pyluach זמינה."""
        try:
            import pyluach  # noqa: F401
            _LOGGER.info("pyluach library found - using accurate Hebrew date conversion")
            return True
        except ImportError:
            _LOGGER.warning(
                "pyluach library not found. Install it for accurate Hebrew date conversion: "
                "pip install pyluach"
            )
            return False

    def gregorian_to_hebrew(self, gregorian_date: date) -> Dict[str, int]:
        """
        המרת תאריך גרגוריאני לתאריך עברי.
        
        Args:
            gregorian_date: תאריך גרגוריאני
            
        Returns:
            dict עם מפתחות: day, month, year
        """
        if self._pyluach_available:
            return self._pyluach_gregorian_to_hebrew(gregorian_date)
        else:
            return self._fallback_gregorian_to_hebrew(gregorian_date)

    def hebrew_to_gregorian(self, day: int, month: int, year: int) -> date:
        """
        המרת תאריך עברי לתאריך גרגוריאני.
        
        Args:
            day: יום בחודש העברי (1-30)
            month: חודש עברי (1-13)
            year: שנה עברית
            
        Returns:
            תאריך גרגוריאני מקביל
        """
        if self._pyluach_available:
            return self._pyluach_hebrew_to_gregorian(day, month, year)
        else:
            return self._fallback_hebrew_to_gregorian(day, month, year)

    def get_current_hebrew_year(self) -> int:
        """מחזיר את השנה העברית הנוכחית."""
        today = date.today()
        hebrew = self.gregorian_to_hebrew(today)
        return hebrew["year"]

    def hebrew_date_to_string(self, day: int, month: int, year: Optional[int] = None) -> str:
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
        day_str = self._number_to_hebrew_letters(day)
        
        if year:
            year_str = self._number_to_hebrew_letters(year % 1000)
            return f"{day_str} ב{month_name} {year_str}"
        else:
            return f"{day_str} ב{month_name}"

    # ============================================================
    # מימוש עם pyluach (מדויק)
    # ============================================================

    def _pyluach_gregorian_to_hebrew(self, gregorian_date: date) -> Dict[str, int]:
        """המרה מגרגוריאני לעברי באמצעות pyluach."""
        try:
            from pyluach.dates import HebrewDate, GregorianDate
            g = GregorianDate(gregorian_date.year, gregorian_date.month, gregorian_date.day)
            h = g.to_heb()
            return {"day": h.day, "month": h.month, "year": h.year}
        except Exception as e:
            _LOGGER.error("pyluach conversion error: %s", e)
            return self._fallback_gregorian_to_hebrew(gregorian_date)

    def _pyluach_hebrew_to_gregorian(self, day: int, month: int, year: int) -> date:
        """המרה מעברי לגרגוריאני באמצעות pyluach."""
        try:
            from pyluach.dates import HebrewDate
            h = HebrewDate(year, month, day)
            g = h.to_greg()
            return date(g.year, g.month, g.day)
        except Exception as e:
            _LOGGER.error("pyluach conversion error: %s", e)
            return self._fallback_hebrew_to_gregorian(day, month, year)

    # ============================================================
    # מימוש fallback (קירוב)
    # ============================================================

    def _fallback_gregorian_to_hebrew(self, gregorian_date: date) -> Dict[str, int]:
        """
        קירוב של המרה מגרגוריאני לעברי ללא ספרייה חיצונית.
        אלגוריתם מבוסס על Meeus, "Astronomical Algorithms".
        """
        jd = self._gregorian_to_jd(gregorian_date.year, gregorian_date.month, gregorian_date.day)
        return self._jd_to_hebrew(jd)

    def _fallback_hebrew_to_gregorian(self, day: int, month: int, year: int) -> date:
        """
        קירוב של המרה מעברי לגרגוריאני ללא ספרייה חיצונית.
        """
        jd = self._hebrew_to_jd(year, month, day)
        return self._jd_to_gregorian(jd)

    def _gregorian_to_jd(self, year: int, month: int, day: int) -> int:
        """המרת תאריך גרגוריאני ל-Julian Day Number."""
        if month <= 2:
            year -= 1
            month += 12
        a = year // 100
        b = 2 - a + a // 4
        return int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524

    def _jd_to_gregorian(self, jd: int) -> date:
        """המרת Julian Day Number לתאריך גרגוריאני."""
        jd = jd + 0.5
        z = int(jd)
        a = int((z - 1867216.25) / 36524.25)
        a = z + 1 + a - a // 4
        b = a + 1524
        c = int((b - 122.1) / 365.25)
        d = int(365.25 * c)
        e = int((b - d) / 30.6001)
        
        day = b - d - int(30.6001 * e)
        month = e - 1 if e < 14 else e - 13
        year = c - 4716 if month > 2 else c - 4715
        
        return date(year, month, day)

    def _hebrew_epoch(self) -> int:
        """Julian Day Number של ראש השנה לבריאה העולם (1 תשרי שנת א׳)."""
        return 347995

    def _is_hebrew_leap_year(self, year: int) -> bool:
        """בדיקה אם שנה עברית היא שנה מעוברת."""
        return ((7 * year) + 1) % 19 < 7

    def _months_in_hebrew_year(self, year: int) -> int:
        """מספר החודשים בשנה עברית."""
        return 13 if self._is_hebrew_leap_year(year) else 12

    def _days_in_hebrew_year(self, year: int) -> int:
        """מספר הימים בשנה עברית."""
        return self._hebrew_to_jd(year + 1, 7, 1) - self._hebrew_to_jd(year, 7, 1)

    def _hebrew_to_jd(self, year: int, month: int, day: int) -> int:
        """המרת תאריך עברי ל-Julian Day Number."""
        months_elapsed = (
            235 * ((year - 1) // 19)
            + 12 * ((year - 1) % 19)
            + ((((year - 1) % 19) * 7 + 1) // 19)
        )
        
        parts = 204 + 793 * (months_elapsed % 1080)
        hours = 5 + 12 * months_elapsed + 793 * (months_elapsed // 1080) + parts // 1080
        conjunction_day = 1 + 29 * months_elapsed + hours // 24
        conjunction_parts = 1080 * (hours % 24) + parts % 1080
        
        alternative_day = conjunction_day
        
        if (
            conjunction_parts >= 19440
            or (conjunction_day % 7 == 2 and conjunction_parts >= 9924 and not self._is_hebrew_leap_year(year))
            or (conjunction_day % 7 == 1 and conjunction_parts >= 16789 and self._is_hebrew_leap_year(year - 1))
        ):
            alternative_day = conjunction_day + 1
        
        if alternative_day % 7 in (0, 3, 5):
            alternative_day += 1
        
        year_jd = alternative_day + self._hebrew_epoch()
        
        # חישוב היום בשנה
        if month < 7:
            months_before = list(range(7, self._months_in_hebrew_year(year) + 1))
            months_before += list(range(1, month))
        else:
            months_before = list(range(7, month))
        
        day_of_year = sum(self._days_in_hebrew_month(m, year) for m in months_before)
        
        return year_jd + day_of_year + day - 1

    def _days_in_hebrew_month(self, month: int, year: int) -> int:
        """מספר הימים בחודש עברי."""
        if month in (1, 3, 5, 7, 11, 13):
            return 30
        elif month in (2, 4, 6, 10, 12):
            return 29
        elif month == 8:
            # חשון - 29 או 30 ימים
            days_in_year = self._days_in_hebrew_year_simple(year)
            return 30 if days_in_year % 10 == 5 else 29
        elif month == 9:
            # כסלו - 29 או 30 ימים
            days_in_year = self._days_in_hebrew_year_simple(year)
            return 29 if days_in_year % 10 == 3 else 30
        return 29

    def _days_in_hebrew_year_simple(self, year: int) -> int:
        """חישוב פשוט של מספר ימים בשנה עברית."""
        months = self._months_in_hebrew_year(year)
        return 354 + (30 if months == 13 else 0)

    def _jd_to_hebrew(self, jd: int) -> Dict[str, int]:
        """המרת Julian Day Number לתאריך עברי."""
        count = (jd - self._hebrew_epoch()) * 98496.0
        elapsed = int(count / 35975351.0)
        year = elapsed - 1
        
        for i in range(elapsed - 1, elapsed + 2):
            if self._hebrew_to_jd(i, 7, 1) <= jd:
                year = i
        
        first = 1 if jd < self._hebrew_to_jd(year, 1, 1) else 7
        month = first
        
        for m in range(first, first + 14):
            m_actual = m if m <= self._months_in_hebrew_year(year) else m - self._months_in_hebrew_year(year)
            if self._hebrew_to_jd(year, m_actual, 1) > jd:
                break
            month = m_actual
        
        day = jd - self._hebrew_to_jd(year, month, 1) + 1
        
        return {"year": year, "month": month, "day": day}

    def _number_to_hebrew_letters(self, num: int) -> str:
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
