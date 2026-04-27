"""Process-wide singletons for the API.

When DATABASE_URL is set:
  - sites/assets rows are upserted at import time
  - the forecast repo is Postgres-backed (Adminer shows runs/points)
  - telemetry is also seeded into telemetry_15m on first import so Adminer is never empty

Otherwise everything stays in-memory (CSV-backed telemetry, in-memory forecasts).
"""
from __future__ import annotations

import logging
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

logger = logging.getLogger(__name__)

CSV_PATH = os.getenv(
    "BESS_CSV_PATH",
    str(Path(__file__).resolve().parents[4] / "data" / "load_timeseries_2025_casestudy.csv"),
)
SITE_NAME = os.getenv("SITE_NAME", "default")
ASSET_NAME = os.getenv("ASSET_NAME", "meter-01")
ASSET_MAX_KW = float(os.getenv("ASSET_MAX_KW", "1000.0"))
DATABASE_URL = os.getenv("DATABASE_URL")

calendar_repo = HolidaysCalendarRepository()


def _bootstrap_postgres() -> tuple[str, str]:
    """Create site/asset rows and seed telemetry into Postgres. Returns (site_uuid, asset_uuid)."""
    from sqlalchemy import create_engine, text
    from bess_forecast.infrastructure.persistence.postgres_telemetry_repository import (
        PostgresTelemetryRepository,
    )

    eng = create_engine(DATABASE_URL, future=True)
    with eng.begin() as conn:
        site_id = conn.execute(text("""
            INSERT INTO sites (name) VALUES (:n)
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING id::text
        """), {"n": SITE_NAME}).scalar_one()
        asset_id = conn.execute(text("""
            INSERT INTO assets (site_id, name, max_kw) VALUES (:s, :n, :m)
            ON CONFLICT (site_id, name) DO UPDATE SET max_kw = EXCLUDED.max_kw
            RETURNING id::text
        """), {"s": site_id, "n": ASSET_NAME, "m": ASSET_MAX_KW}).scalar_one()
        existing = conn.execute(text(
            "SELECT count(*) FROM telemetry_15m WHERE site_id = :s"
        ), {"s": site_id}).scalar_one()

    if existing == 0:
        logger.info("Seeding telemetry into Postgres (one-time)…")
        from bess_forecast.domain.entities.telemetry import TelemetryReading
        from bess_forecast.infrastructure.persistence.csv_telemetry_repository import (
            load_csv,
        )
        s = load_csv(CSV_PATH)
        readings = [
            TelemetryReading(site_id, asset_id, ts.to_pydatetime(), float(v))
            for ts, v in s.items()
        ]
        repo = PostgresTelemetryRepository(DATABASE_URL)
        repo.save_many(readings)
        logger.info("Seeded %d telemetry rows", len(readings))
    return site_id, asset_id


agent_repo = None  # populated when Postgres is available

if DATABASE_URL:
    try:
        SITE_ID, ASSET_ID = _bootstrap_postgres()
        from bess_forecast.infrastructure.persistence.postgres_agent_repository import (
            PostgresAgentRepository,
        )
        from bess_forecast.infrastructure.persistence.postgres_forecast_repository import (
            PostgresForecastRepository,
        )
        from bess_forecast.infrastructure.persistence.postgres_telemetry_repository import (
            PostgresTelemetryRepository,
        )
        forecast_repo = PostgresForecastRepository(DATABASE_URL)
        telemetry_repo = PostgresTelemetryRepository(DATABASE_URL)
        agent_repo = PostgresAgentRepository(DATABASE_URL)
        logger.info("Repos: Postgres @ %s", DATABASE_URL.split("@")[-1])
    except Exception as e:
        logger.warning("Postgres bootstrap failed (%s); falling back to in-memory", e)
        SITE_ID, ASSET_ID = SITE_NAME, ASSET_NAME
        forecast_repo = InMemoryForecastRepository()
        telemetry_repo = CsvTelemetryRepository(CSV_PATH, site_id=SITE_ID, asset_id=ASSET_ID)
else:
    SITE_ID, ASSET_ID = SITE_NAME, ASSET_NAME
    forecast_repo = InMemoryForecastRepository()
    telemetry_repo = CsvTelemetryRepository(CSV_PATH, site_id=SITE_ID, asset_id=ASSET_ID)
    logger.info("Repos: in-memory (set DATABASE_URL to persist)")
