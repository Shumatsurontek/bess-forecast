from abc import ABC, abstractmethod
from datetime import datetime

from bess_forecast.domain.entities.telemetry import TelemetryReading


class TelemetryRepository(ABC):
    @abstractmethod
    def load(
        self, site_id: str, since: datetime, until: datetime
    ) -> list[TelemetryReading]: ...

    @abstractmethod
    def save_many(self, readings: list[TelemetryReading]) -> int: ...
