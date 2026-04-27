"""In-memory forecast repository — used by CLI/agent when Postgres isn't running."""
from __future__ import annotations

import json
from pathlib import Path

from bess_forecast.domain.entities.forecast import ForecastPoint, ForecastRun
from bess_forecast.domain.ports.forecast_repository import ForecastRepository


class InMemoryForecastRepository(ForecastRepository):
    def __init__(self) -> None:
        self._runs: dict[str, ForecastRun] = {}
        self._points: dict[str, list[ForecastPoint]] = {}

    def save(self, run: ForecastRun, points: list[ForecastPoint]) -> None:
        self._runs[run.id] = run
        self._points[run.id] = list(points)

    def get_run(self, run_id: str) -> ForecastRun | None:
        return self._runs.get(run_id)

    def list_points(self, run_id: str) -> list[ForecastPoint]:
        return list(self._points.get(run_id, []))

    def list_runs(self) -> list[ForecastRun]:
        return list(self._runs.values())

    def dump_jsonl(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for run in self._runs.values():
                f.write(json.dumps({
                    "kind": "run",
                    "id": run.id,
                    "site_id": run.site_id,
                    "generated_at": run.generated_at.isoformat(),
                    "horizon_start": run.horizon_start.isoformat(),
                    "horizon_end": run.horizon_end.isoformat(),
                    "model_name": run.model_name,
                    "model_version": run.model_version,
                    "quantile": run.quantile,
                    "metrics": run.metrics,
                }) + "\n")
                for p in self._points[run.id]:
                    f.write(json.dumps({
                        "kind": "point",
                        "run_id": run.id,
                        "ts": p.ts.isoformat(),
                        "kw_pred": p.kw_pred,
                    }) + "\n")
