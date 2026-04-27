"""Explicit wiring — no DI container."""
from __future__ import annotations

import os

from bess_forecast.infrastructure.agent.tools import configure_tools
from bess_forecast.infrastructure.persistence.holidays_calendar_repository import (
    HolidaysCalendarRepository,
)


def wire_agent_with_postgres() -> None:
    from bess_forecast.infrastructure.persistence.postgres_forecast_repository import (
        PostgresForecastRepository,
    )
    from bess_forecast.infrastructure.persistence.postgres_telemetry_repository import (
        PostgresTelemetryRepository,
    )
    url = os.environ["DATABASE_URL"]
    configure_tools(
        forecast_repo=PostgresForecastRepository(url),
        telemetry_repo=PostgresTelemetryRepository(url),
        calendar_repo=HolidaysCalendarRepository(),
    )


def wire_agent_with_inmemory(forecast_repo, telemetry_repo) -> None:
    configure_tools(
        forecast_repo=forecast_repo,
        telemetry_repo=telemetry_repo,
        calendar_repo=HolidaysCalendarRepository(),
    )
