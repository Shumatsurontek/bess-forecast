from abc import ABC, abstractmethod
from datetime import datetime


class CalendarRepository(ABC):
    @abstractmethod
    def is_german_holiday(self, date: datetime) -> bool: ...

    @abstractmethod
    def is_dst_switch(self, date: datetime) -> bool: ...
