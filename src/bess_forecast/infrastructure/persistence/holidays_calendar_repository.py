"""Calendar repository backed by python-holidays (Germany)."""
from __future__ import annotations

from datetime import datetime, timedelta

import holidays

from bess_forecast.domain.ports.calendar_repository import CalendarRepository


class HolidaysCalendarRepository(CalendarRepository):
    def __init__(self, country: str = "DE") -> None:
        self._country = country
        self._cache: dict[int, holidays.HolidayBase] = {}

    def _holidays(self, year: int) -> holidays.HolidayBase:
        if year not in self._cache:
            self._cache[year] = holidays.country_holidays(self._country, years=[year])
        return self._cache[year]

    def is_german_holiday(self, date: datetime) -> bool:
        return date.date() in self._holidays(date.year)

    def is_dst_switch(self, date: datetime) -> bool:
        d = date.date()
        if d.weekday() != 6:
            return False
        if d.month == 3 and d.day >= 25:
            return True
        if d.month == 10 and d.day >= 25:
            return True
        return False

    def german_holidays_for(self, year: int) -> list[datetime]:
        return [
            datetime(d.year, d.month, d.day) for d in self._holidays(year)
        ]
