from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query

from bess_forecast.infrastructure.api import state
from bess_forecast.infrastructure.api.schemas import TelemetryDTO

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.get("", response_model=list[TelemetryDTO])
def get_telemetry(
    since: datetime = Query(...),
    until: datetime = Query(...),
) -> list[TelemetryDTO]:
    readings = state.telemetry_repo.load(state.SITE_NAME, since, until)
    return [TelemetryDTO(ts=r.ts, kw=r.kw, quality_flag=r.quality_flag) for r in readings]
