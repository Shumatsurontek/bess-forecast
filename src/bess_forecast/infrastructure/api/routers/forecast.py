from __future__ import annotations

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

from bess_forecast.application.use_cases.run_forecast import run_forecast
from bess_forecast.infrastructure.api import state
from bess_forecast.infrastructure.api.jobs import JobBusProgressSink, bus
from bess_forecast.infrastructure.api.schemas import (
    ForecastPointDTO,
    ForecastResponse,
    ForecastRunDTO,
    JobAcceptedDTO,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/forecast", tags=["forecast"])


class TriggerRunRequest(BaseModel):
    asof: datetime
    model: str = "lgbm"


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


@router.post("/run", response_model=JobAcceptedDTO)
def trigger_run(
    asof: datetime = Query(..., description="Forecast as-of timestamp"),
    model: str = Query("lgbm", pattern="^(naive|lgbm|timesfm)$"),
    tasks: BackgroundTasks = None,
) -> JobAcceptedDTO:
    """Kick off a forecast in the background. Stream progress over /ws/jobs/{job_id}."""
    job_id = bus.new_job_id()
    run_id = str(uuid.uuid4())  # pre-allocate so the front can navigate immediately
    sink = JobBusProgressSink(bus, job_id)

    def _work() -> None:
        try:
            run_forecast(
                csv_path=state.CSV_PATH,
                site_id=state.SITE_ID,
                asset_id=state.ASSET_ID,
                asof=asof,
                model_name=model,
                asset_max_kw=state.ASSET_MAX_KW,
                forecast_repo=state.forecast_repo,
                progress=sink,
                run_id=run_id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("forecast job %s failed", job_id)
            sink.emit("error", str(exc), extra={"type": exc.__class__.__name__})
        finally:
            bus.close(job_id)

    tasks.add_task(_work)
    return JobAcceptedDTO(job_id=job_id, run_id=run_id)


@router.post("/run-sync", response_model=ForecastResponse)
def trigger_run_sync(
    asof: datetime = Query(...),
    model: str = Query("lgbm", pattern="^(naive|lgbm|timesfm)$"),
) -> ForecastResponse:
    """Synchronous variant — useful for the CLI / smoke tests."""
    result = run_forecast(
        csv_path=state.CSV_PATH,
        site_id=state.SITE_ID,
        asset_id=state.ASSET_ID,
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
