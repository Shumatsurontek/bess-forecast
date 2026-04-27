"""Postgres telemetry repository (psycopg3 + SQLAlchemy core)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from bess_forecast.domain.entities.telemetry import TelemetryReading
from bess_forecast.domain.ports.telemetry_repository import TelemetryRepository


class PostgresTelemetryRepository(TelemetryRepository):
    def __init__(self, url: str) -> None:
        self._engine: Engine = create_engine(url, future=True, pool_pre_ping=True)

    def load(
        self, site_id: str, since: datetime, until: datetime
    ) -> list[TelemetryReading]:
        sql = text("""
            SELECT site_id::text, asset_id::text, ts, kw, quality_flag
            FROM telemetry_15m
            WHERE site_id = :site_id AND ts BETWEEN :since AND :until
            ORDER BY ts
        """)
        with self._engine.connect() as conn:
            rows = conn.execute(
                sql, {"site_id": site_id, "since": since, "until": until}
            ).all()
        return [
            TelemetryReading(r[0], r[1], r[2], float(r[3]), int(r[4])) for r in rows
        ]

    def save_many(self, readings: list[TelemetryReading]) -> int:
        if not readings:
            return 0
        sql = text("""
            INSERT INTO telemetry_15m (site_id, asset_id, ts, kw, quality_flag)
            VALUES (:site_id, :asset_id, :ts, :kw, :quality_flag)
            ON CONFLICT (site_id, asset_id, ts) DO UPDATE
                SET kw = EXCLUDED.kw, quality_flag = EXCLUDED.quality_flag
        """)
        with self._engine.begin() as conn:
            conn.execute(sql, [
                {"site_id": r.site_id, "asset_id": r.asset_id, "ts": r.ts,
                 "kw": r.kw, "quality_flag": r.quality_flag}
                for r in readings
            ])
        return len(readings)
