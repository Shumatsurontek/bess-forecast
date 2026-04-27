from __future__ import annotations

from fastapi import APIRouter, HTTPException

from bess_forecast.infrastructure.agent.tools import configure_tools
from bess_forecast.infrastructure.api import state
from bess_forecast.infrastructure.api.schemas import DiagnosticResponse

router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])


@router.post("/{run_id}", response_model=DiagnosticResponse)
def diagnose(run_id: str) -> DiagnosticResponse:
    if state.forecast_repo.get_run(run_id) is None:
        raise HTTPException(404, f"Run {run_id} not found")
    configure_tools(
        forecast_repo=state.forecast_repo,
        telemetry_repo=state.telemetry_repo,
        calendar_repo=state.calendar_repo,
    )
    from bess_forecast.application.use_cases.run_diagnostic import run_diagnostic
    report = run_diagnostic(run_id, site_id=state.SITE_NAME)
    return DiagnosticResponse(run_id=run_id, report_markdown=report)
