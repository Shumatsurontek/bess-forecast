"""End-to-end forecast pipeline: load → validate → features → fit → predict → save."""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from bess_forecast.application.services.feature_service import (
    FEATURE_COLS,
    QUARTERS_PER_DAY,
    build_features,
)
from bess_forecast.application.services.metrics_service import compute_peak_metrics
from bess_forecast.application.services.validation_service import validate
from bess_forecast.domain.entities.forecast import ForecastPoint, ForecastRun
from bess_forecast.domain.entities.telemetry import TelemetryReading
from bess_forecast.domain.ports.forecast_repository import ForecastRepository
from bess_forecast.domain.ports.model_port import ModelPort
from bess_forecast.infrastructure.persistence.csv_telemetry_repository import (
    CsvTelemetryRepository,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ForecastResult:
    run: ForecastRun
    points: list[ForecastPoint]
    metrics: dict


def _build_model(name: str, quantile: float, horizon: int) -> ModelPort:
    if name == "naive":
        from bess_forecast.infrastructure.models.naive_baseline import NaiveBaseline
        return NaiveBaseline()
    if name == "lgbm":
        from bess_forecast.infrastructure.models.lightgbm_quantile import (
            LightGBMQuantile,
        )
        return LightGBMQuantile(quantile=quantile)
    if name == "timesfm":
        from bess_forecast.infrastructure.models.timesfm_zeroshot import (
            TimesFMZeroShot,
        )
        return TimesFMZeroShot(horizon=horizon)
    raise ValueError(f"Unknown model: {name}")


def run_forecast(
    *,
    csv_path: str | Path,
    site_id: str,
    asset_id: str,
    asof: datetime,
    model_name: str = "lgbm",
    horizon_quarters: int = QUARTERS_PER_DAY,
    quantile: float = 0.75,
    asset_max_kw: float = 200.0,
    forecast_repo: ForecastRepository | None = None,
) -> ForecastResult:
    csv_repo = CsvTelemetryRepository(csv_path, site_id=site_id, asset_id=asset_id)
    series = csv_repo.as_series()

    # Use only history up to `asof` for fitting; horizon = (asof, asof+24h]
    if asof.tzinfo is None:
        asof = pd.Timestamp(asof).tz_localize(series.index.tz).to_pydatetime()
    history = series.loc[series.index <= asof]
    horizon_start = asof + timedelta(minutes=15)
    horizon_end = asof + timedelta(minutes=15 * horizon_quarters)
    actual_horizon = series.loc[
        (series.index >= horizon_start) & (series.index <= horizon_end)
    ]

    report = validate(history, max_kw=asset_max_kw)
    if report.is_blocking:
        msgs = "; ".join(f"{i.rule}: {i.message}" for i in report.issues
                         if i.severity.value == "BLOCKING")
        raise RuntimeError(f"Validation blocked the run: {msgs}")
    logger.info("Validation: %d warnings, 0 blocking", report.warning_count)

    features = build_features(history)
    train = features.dropna(subset=FEATURE_COLS + ["y"])
    X_train, y_train = train[FEATURE_COLS], train["y"]

    model = _build_model(model_name, quantile=quantile, horizon=horizon_quarters)
    model.fit(X_train, y_train)

    horizon_index = pd.date_range(
        horizon_start, periods=horizon_quarters, freq="15min", tz=series.index.tz
    )
    if model_name == "lgbm":
        # Recursive 1-step-ahead prediction so lag features stay valid.
        ext = history.copy()
        preds = []
        for ts in horizon_index:
            ext_features = build_features(
                pd.concat([ext, pd.Series([np.nan], index=[ts])])
            )
            x = ext_features.loc[[ts], FEATURE_COLS].fillna(method="ffill")
            yhat = float(model.predict(x)[0])
            preds.append(yhat)
            ext = pd.concat([ext, pd.Series([yhat], index=[ts])])
        preds_arr = np.array(preds)
    else:
        preds_arr = model.predict(pd.DataFrame(index=horizon_index))

    points = [
        ForecastPoint(ts=ts.to_pydatetime(), kw_pred=float(p))
        for ts, p in zip(horizon_index, preds_arr)
    ]

    actuals_list: list[TelemetryReading] = [
        TelemetryReading(site_id, asset_id, ts.to_pydatetime(), float(v))
        for ts, v in actual_horizon.items()
    ]
    threshold_kw = (
        float(np.quantile([r.kw for r in actuals_list], 0.85))
        if actuals_list else float(np.quantile(history.dropna(), 0.85))
    )
    pm = compute_peak_metrics(points, actuals_list,
                              threshold_kw=threshold_kw, quantile=quantile)

    metrics = {
        "pinball_loss": pm.pinball_loss,
        "rmse": pm.rmse,
        "mae": pm.mae,
        "peaks_captured": pm.captured,
        "peaks_total": pm.total_peaks,
        "peak_capture_rate": pm.capture_rate,
        "threshold_kw": pm.threshold_kw,
    }

    run = ForecastRun(
        id=str(uuid.uuid4()),
        site_id=site_id,
        generated_at=asof,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        model_name=model.name,
        model_version=model.version,
        quantile=quantile if model_name != "naive" else None,
        metrics=metrics,
    )
    if forecast_repo is not None:
        forecast_repo.save(run, points)
    return ForecastResult(run=run, points=points, metrics=metrics)
