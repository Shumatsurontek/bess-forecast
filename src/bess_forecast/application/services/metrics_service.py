"""Forecast vs actual metrics: pinball loss, RMSE, MAE, peak capture rate."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

from bess_forecast.domain.entities.forecast import ForecastPoint
from bess_forecast.domain.entities.telemetry import TelemetryReading


@dataclass(frozen=True)
class PeakIncident:
    ts: datetime
    predicted_kw: float
    actual_kw: float
    gap_kw: float  # negative = under-forecast (missed peak); positive = over-forecast


@dataclass(frozen=True)
class PeakMetrics:
    captured: int
    total_peaks: int
    pinball_loss: float
    rmse: float
    mae: float
    threshold_kw: float
    incidents: list[PeakIncident] = field(default_factory=list)

    @property
    def capture_rate(self) -> float:
        return self.captured / self.total_peaks if self.total_peaks else float("nan")


def _pinball(predicted: float, actual: float, q: float) -> float:
    diff = actual - predicted
    return max(q * diff, (q - 1) * diff)


def compute_peak_metrics(
    forecast: list[ForecastPoint],
    actuals: list[TelemetryReading],
    *,
    threshold_kw: float,
    quantile: float = 0.75,
    over_tol_kw: float = 50.0,
) -> PeakMetrics:
    by_ts = {r.ts: r.kw for r in actuals}
    aligned = [(p.ts, p.kw_pred, by_ts[p.ts]) for p in forecast if p.ts in by_ts]
    if not aligned:
        return PeakMetrics(0, 0, 0.0, 0.0, 0.0, threshold_kw, [])

    preds = np.array([p for _, p, _ in aligned], dtype=float)
    acts = np.array([a for _, _, a in aligned], dtype=float)

    pinball = float(np.mean([_pinball(p, a, quantile) for p, a in zip(preds, acts)]))
    rmse = float(np.sqrt(np.mean((preds - acts) ** 2)))
    mae = float(np.mean(np.abs(preds - acts)))

    captured = 0
    total_peaks = 0
    incidents: list[PeakIncident] = []
    for ts, pred, act in aligned:
        is_peak = act >= threshold_kw
        if is_peak:
            total_peaks += 1
            if pred >= threshold_kw:
                captured += 1
            else:
                incidents.append(PeakIncident(ts, pred, act, pred - act))
        elif (pred - act) > over_tol_kw:
            incidents.append(PeakIncident(ts, pred, act, pred - act))

    return PeakMetrics(
        captured=captured,
        total_peaks=total_peaks,
        pinball_loss=pinball,
        rmse=rmse,
        mae=mae,
        threshold_kw=threshold_kw,
        incidents=incidents,
    )
