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
from bess_forecast.domain.entities.progress_stage import ForecastStage
from bess_forecast.domain.entities.telemetry import TelemetryReading
from bess_forecast.domain.ports.forecast_repository import ForecastRepository
from bess_forecast.domain.ports.model_port import ModelPort
from bess_forecast.domain.ports.progress_sink import NoopProgressSink, ProgressSink
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
    progress: ProgressSink | None = None,
    run_id: str | None = None,
) -> ForecastResult:
    progress = progress or NoopProgressSink()
    progress.emit(ForecastStage.LOADING_CSV, "reading CSV", pct=0.05)
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

    progress.emit(ForecastStage.VALIDATING_RAW, "running rules on raw history", pct=0.15)
    report = validate(history, max_kw=asset_max_kw)
    logger.info("Validation: %d warnings, %d blocking",
                report.warning_count, report.blocking_count)

    progress.emit(
        ForecastStage.REPAIRING,
        f"sanitizing series ({report.blocking_count} blocking, {report.warning_count} warnings)",
        pct=0.25,
        extra={"blocking": report.blocking_count, "warnings": report.warning_count},
    )
    # Fail-safe repair: sentinel + sign + gap fill.
    history = history.where(history < asset_max_kw)            # drop sentinels
    history = history.clip(lower=0.0)                          # negatives → 0
    full_idx = pd.date_range(history.index.min(), history.index.max(),
                             freq="15min", tz=history.index.tz)
    history = history.reindex(full_idx).ffill().bfill()

    progress.emit(ForecastStage.VALIDATING_POST, "re-validating repaired series", pct=0.35)
    post = validate(history, max_kw=asset_max_kw)
    if post.is_blocking:
        msgs = "; ".join(f"{i.rule}: {i.message}" for i in post.issues
                         if i.severity.value == "BLOCKING")
        raise RuntimeError(f"Validation blocked the run after repair: {msgs}")

    progress.emit(ForecastStage.BUILDING_FEATURES, "lags + calendar features", pct=0.45)
    features = build_features(history)
    train = features.dropna(subset=FEATURE_COLS + ["y"])
    X_train, y_train = train[FEATURE_COLS], train["y"]

    progress.emit(ForecastStage.FITTING, f"training {model_name}", pct=0.55,
                  extra={"n_samples": int(len(X_train))})
    model = _build_model(model_name, quantile=quantile, horizon=horizon_quarters)
    model.fit(X_train, y_train)

    progress.emit(ForecastStage.PREDICTING, f"predicting {horizon_quarters} quarter-hours", pct=0.75)
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
            x = ext_features.loc[[ts], FEATURE_COLS].ffill().bfill()
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
    progress.emit(ForecastStage.COMPUTING_METRICS, "pinball + peak capture", pct=0.9)
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
        id=run_id or str(uuid.uuid4()),
        site_id=site_id,
        generated_at=asof,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        model_name=model.name,
        model_version=model.version,
        quantile=quantile if model_name != "naive" else None,
        metrics=metrics,
    )
    progress.emit(ForecastStage.SAVING, "persisting run + points", pct=0.97,
                  extra={"run_id": run.id})
    if forecast_repo is not None:
        forecast_repo.save(run, points)
    progress.emit(ForecastStage.DONE, "complete", pct=1.0,
                  extra={"run_id": run.id, "metrics": metrics})
    return ForecastResult(run=run, points=points, metrics=metrics)
