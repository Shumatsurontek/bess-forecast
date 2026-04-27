"""E2E mocked: verify agent wiring and LangSmith config without calling OpenAI."""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from bess_forecast.application.services.metrics_service import compute_peak_metrics
from bess_forecast.domain.entities.forecast import ForecastPoint
from bess_forecast.domain.entities.telemetry import TelemetryReading


def test_peak_metrics_detects_missed_peak():
    base = datetime(2025, 12, 26, 12, 0, tzinfo=timezone.utc)
    forecast = [ForecastPoint(ts=base, kw_pred=200.0)]
    actuals = [TelemetryReading("s", "a", base, 500.0)]
    m = compute_peak_metrics(forecast, actuals, threshold_kw=400.0)
    assert m.total_peaks == 1
    assert m.captured == 0
    assert len(m.incidents) == 1


def test_peak_metrics_detects_over_forecast():
    base = datetime(2025, 12, 26, 3, 0, tzinfo=timezone.utc)
    forecast = [ForecastPoint(ts=base, kw_pred=350.0)]
    actuals = [TelemetryReading("s", "a", base, 200.0)]
    m = compute_peak_metrics(forecast, actuals, threshold_kw=400.0,
                             over_tol_kw=50.0)
    assert m.total_peaks == 0
    assert len(m.incidents) == 1
    assert m.incidents[0].gap_kw == 150.0


@patch("bess_forecast.application.use_cases.run_diagnostic.create_react_agent")
@patch("bess_forecast.application.use_cases.run_diagnostic.create_llm")
def test_run_diagnostic_passes_langsmith_config(mock_llm, mock_create_agent):
    mock_agent = MagicMock()
    mock_agent.invoke.return_value = {
        "messages": [MagicMock(content="## Summary\nCaptured 0/1 peaks.")]
    }
    mock_create_agent.return_value = mock_agent
    mock_llm.return_value.model_name = "gpt-4o-mini"

    from bess_forecast.application.use_cases.run_diagnostic import run_diagnostic
    report = run_diagnostic("abc-123", site_id="site-001")

    assert "Summary" in report
    cfg = mock_agent.invoke.call_args.kwargs["config"]
    assert cfg["metadata"]["run_id"] == "abc-123"
    assert cfg["metadata"]["site_id"] == "site-001"
    assert "agent:forecast-diagnostic" in cfg["tags"]
    assert cfg["run_name"] == "diagnostic:forecast-diagnostic"
