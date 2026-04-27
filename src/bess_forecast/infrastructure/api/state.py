"""Process-wide singletons for the API.

Backed by an in-memory forecast repo so the API works without Postgres for the
case-study demo. Swap with Postgres impls in production.
"""
from __future__ import annotations

import os
from pathlib import Path

from bess_forecast.infrastructure.persistence.csv_telemetry_repository import (
    CsvTelemetryRepository,
)
from bess_forecast.infrastructure.persistence.holidays_calendar_repository import (
    HolidaysCalendarRepository,
)
from bess_forecast.infrastructure.persistence.inmemory_forecast_repository import (
    InMemoryForecastRepository,
)

CSV_PATH = os.getenv(
    "BESS_CSV_PATH",
    str(Path(__file__).resolve().parents[3].parent / "data" / "load_timeseries_2025_casestudy.csv"),
)
SITE_NAME = os.getenv("SITE_NAME", "default")
ASSET_NAME = os.getenv("ASSET_NAME", "meter-01")
ASSET_MAX_KW = float(os.getenv("ASSET_MAX_KW", "200.0"))

forecast_repo = InMemoryForecastRepository()
telemetry_repo = CsvTelemetryRepository(
    CSV_PATH, site_id=SITE_NAME, asset_id=ASSET_NAME
)
calendar_repo = HolidaysCalendarRepository()
