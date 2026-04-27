from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from bess_forecast.application.use_cases.run_forecast import run_forecast
from bess_forecast.infrastructure.api import state
from bess_forecast.infrastructure.api.schemas import (
    ForecastPointDTO,
    ForecastResponse,
    ForecastRunDTO,
)

router = APIRouter(prefix="/forecast", tags=["forecast"])


def _to_dto(run, points) -> ForecastResponse:
    return ForecastResponse(
        run=ForecastRunDTO(
            id=run.id, site_id=run.site_id, generated_at=run.generated_at,
            horizon_start=run.horizon_start, horizon_end=run.horizon_end,
            model_name=run.model_name, model_version=run.model_version,
            quantile=run.quantile, metrics=run.metrics,
        ),
        points=[ForecastPointDTO(ts=p.ts, kw_pred=p.kw_pred) for p in points],
    )


@router.post("/run", response_model=ForecastResponse)
def trigger_run(
    asof: datetime = Query(..., description="Forecast as-of timestamp"),
    model: str = Query("lgbm", pattern="^(naive|lgbm|timesfm)$"),
) -> ForecastResponse:
    result = run_forecast(
        csv_path=state.CSV_PATH,
        site_id=state.SITE_NAME,
        asset_id=state.ASSET_NAME,
        asof=asof,
        model_name=model,
        asset_max_kw=state.ASSET_MAX_KW,
        forecast_repo=state.forecast_repo,
    )
    return _to_dto(result.run, result.points)


@router.get("/runs", response_model=list[ForecastRunDTO])
def list_runs() -> list[ForecastRunDTO]:
    return [
        ForecastRunDTO(
            id=r.id, site_id=r.site_id, generated_at=r.generated_at,
            horizon_start=r.horizon_start, horizon_end=r.horizon_end,
            model_name=r.model_name, model_version=r.model_version,
            quantile=r.quantile, metrics=r.metrics,
        )
        for r in state.forecast_repo.list_runs()
    ]


@router.get("/{run_id}", response_model=ForecastResponse)
def get_run(run_id: str) -> ForecastResponse:
    run = state.forecast_repo.get_run(run_id)
    if run is None:
        raise HTTPException(404, f"Run {run_id} not found")
    points = state.forecast_repo.list_points(run_id)
    return _to_dto(run, points)
