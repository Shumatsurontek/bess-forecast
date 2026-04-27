from abc import ABC, abstractmethod

from bess_forecast.domain.entities.forecast import ForecastPoint, ForecastRun


class ForecastRepository(ABC):
    @abstractmethod
    def save(self, run: ForecastRun, points: list[ForecastPoint]) -> None: ...

    @abstractmethod
    def get_run(self, run_id: str) -> ForecastRun | None: ...

    @abstractmethod
    def list_points(self, run_id: str) -> list[ForecastPoint]: ...
