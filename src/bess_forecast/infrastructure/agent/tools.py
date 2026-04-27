"""LangChain tools — bind the domain ports. Read-only by design."""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from bess_forecast.application.services.metrics_service import compute_peak_metrics

_forecast_repo = None
_telemetry_repo = None
_calendar_repo = None


def configure_tools(*, forecast_repo, telemetry_repo, calendar_repo) -> None:
    """Bind concrete repos. Call once at startup."""
    global _forecast_repo, _telemetry_repo, _calendar_repo
    _forecast_repo = forecast_repo
    _telemetry_repo = telemetry_repo
    _calendar_repo = calendar_repo


def _dump(obj) -> str:
    def default(o):
        if isinstance(o, datetime):
            return o.isoformat()
        if hasattr(o, "__dataclass_fields__"):
            return asdict(o)
        return str(o)
    return json.dumps(obj, default=default)


class GetForecastRunInput(BaseModel):
    run_id: str = Field(description="UUID of the forecast run")


@tool(args_schema=GetForecastRunInput)
def get_forecast_run(run_id: str) -> str:
    """Retrieve metadata + predicted points for a forecast run."""
    run = _forecast_repo.get_run(run_id)
    if run is None:
        return _dump({"error": f"Run {run_id} not found"})
    points = _forecast_repo.list_points(run_id)
    return _dump({
        "run": asdict(run),
        "points": [asdict(p) for p in points[:200]],
        "total_points": len(points),
    })


class GetActualsInput(BaseModel):
    site_id: str
    since: str = Field(description="ISO datetime, inclusive")
    until: str = Field(description="ISO datetime, inclusive")


@tool(args_schema=GetActualsInput)
def get_actuals(site_id: str, since: str, until: str) -> str:
    """Retrieve actual telemetry readings for a site over a time window."""
    readings = _telemetry_repo.load(
        site_id, datetime.fromisoformat(since), datetime.fromisoformat(until)
    )
    return _dump([asdict(r) for r in readings])


class ComputePeakMetricsInput(BaseModel):
    run_id: str
    threshold_kw: float = Field(
        description="Peak-shaving threshold in kW (e.g. 0.85 * max(actuals))"
    )


@tool(args_schema=ComputePeakMetricsInput)
def compute_peak_metrics_tool(run_id: str, threshold_kw: float) -> str:
    """Compare forecast vs actuals: capture rate, pinball loss, incident list."""
    run = _forecast_repo.get_run(run_id)
    if run is None:
        return _dump({"error": f"Run {run_id} not found"})
    points = _forecast_repo.list_points(run_id)
    actuals = _telemetry_repo.load(run.site_id, run.horizon_start, run.horizon_end)
    m = compute_peak_metrics(points, actuals, threshold_kw=threshold_kw)
    return _dump({
        "captured": m.captured,
        "total_peaks": m.total_peaks,
        "pinball_loss": round(m.pinball_loss, 3),
        "rmse": round(m.rmse, 3),
        "mae": round(m.mae, 3),
        "threshold_kw": m.threshold_kw,
        "incidents": [asdict(i) for i in m.incidents],
    })


class GetCalendarInput(BaseModel):
    date: str = Field(description="ISO date (yyyy-mm-dd)")


@tool(args_schema=GetCalendarInput)
def get_calendar_context(date: str) -> str:
    """Holiday and DST flags for a given German calendar date."""
    d = datetime.fromisoformat(date)
    return _dump({
        "date": d.date().isoformat(),
        "weekday": d.strftime("%A"),
        "is_holiday": _calendar_repo.is_german_holiday(d),
        "is_dst_switch": _calendar_repo.is_dst_switch(d),
    })


ALL_TOOLS = [
    get_forecast_run, get_actuals, compute_peak_metrics_tool, get_calendar_context,
]
