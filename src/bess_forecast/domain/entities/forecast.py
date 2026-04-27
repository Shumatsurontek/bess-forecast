from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ForecastPoint:
    ts: datetime
    kw_pred: float


@dataclass(frozen=True)
class ForecastRun:
    id: str
    site_id: str
    generated_at: datetime
    horizon_start: datetime
    horizon_end: datetime
    model_name: str
    model_version: str
    quantile: float | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
