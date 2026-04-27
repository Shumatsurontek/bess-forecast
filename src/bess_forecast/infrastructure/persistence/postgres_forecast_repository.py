"""Postgres forecast repository."""
from __future__ import annotations

import json

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from bess_forecast.domain.entities.forecast import ForecastPoint, ForecastRun
from bess_forecast.domain.ports.forecast_repository import ForecastRepository


class PostgresForecastRepository(ForecastRepository):
    def __init__(self, url: str) -> None:
        self._engine: Engine = create_engine(url, future=True)

    def save(self, run: ForecastRun, points: list[ForecastPoint]) -> None:
        with self._engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO forecast_runs (id, site_id, generated_at,
                    horizon_start, horizon_end, model_name, model_version,
                    quantile, metrics)
                VALUES (:id, :site_id, :generated_at, :horizon_start,
                    :horizon_end, :model_name, :model_version, :quantile,
                    CAST(:metrics AS JSONB))
                ON CONFLICT (site_id, generated_at, model_version, quantile)
                    DO UPDATE SET metrics = EXCLUDED.metrics
            """), {
                "id": run.id, "site_id": run.site_id,
                "generated_at": run.generated_at,
                "horizon_start": run.horizon_start, "horizon_end": run.horizon_end,
                "model_name": run.model_name, "model_version": run.model_version,
                "quantile": run.quantile, "metrics": json.dumps(run.metrics),
            })
            if points:
                conn.execute(text("""
                    INSERT INTO forecast_points (run_id, ts, kw_pred)
                    VALUES (:run_id, :ts, :kw_pred)
                    ON CONFLICT (run_id, ts) DO UPDATE SET kw_pred = EXCLUDED.kw_pred
                """), [{"run_id": run.id, "ts": p.ts, "kw_pred": p.kw_pred}
                       for p in points])

    def get_run(self, run_id: str) -> ForecastRun | None:
        sql = text("""
            SELECT id::text, site_id::text, generated_at, horizon_start,
                   horizon_end, model_name, model_version, quantile, metrics
            FROM forecast_runs WHERE id = :id
        """)
        with self._engine.connect() as conn:
            row = conn.execute(sql, {"id": run_id}).first()
        if not row:
            return None
        return ForecastRun(
            id=row[0], site_id=row[1], generated_at=row[2],
            horizon_start=row[3], horizon_end=row[4],
            model_name=row[5], model_version=row[6], quantile=row[7],
            metrics=row[8] or {},
        )

    def list_points(self, run_id: str) -> list[ForecastPoint]:
        sql = text("""
            SELECT ts, kw_pred FROM forecast_points
            WHERE run_id = :id ORDER BY ts
        """)
        with self._engine.connect() as conn:
            rows = conn.execute(sql, {"id": run_id}).all()
        return [ForecastPoint(ts=r[0], kw_pred=float(r[1])) for r in rows]

    def get_active_at(self, site_id: str, at):
        """Return the most recent run with generated_at <= `at`."""
        sql = text("""
            SELECT id::text FROM forecast_runs
            WHERE site_id = :site_id AND generated_at <= :at
            ORDER BY generated_at DESC LIMIT 1
        """)
        with self._engine.connect() as conn:
            row = conn.execute(sql, {"site_id": site_id, "at": at}).first()
        return self.get_run(row[0]) if row else None
