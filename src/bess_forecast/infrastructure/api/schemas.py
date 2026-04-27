from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ForecastPointDTO(BaseModel):
    ts: datetime
    kw_pred: float


class ForecastRunDTO(BaseModel):
    id: str
    site_id: str
    generated_at: datetime
    horizon_start: datetime
    horizon_end: datetime
    model_name: str
    model_version: str
    quantile: float | None
    metrics: dict[str, Any]


class ForecastResponse(BaseModel):
    run: ForecastRunDTO
    points: list[ForecastPointDTO]


class TelemetryDTO(BaseModel):
    ts: datetime
    kw: float
    quality_flag: int = 0


class ValidationIssueDTO(BaseModel):
    rule: str
    severity: str
    message: str
    affected_count: int
    sample: list[str]


class ValidationReportDTO(BaseModel):
    issues: list[ValidationIssueDTO]
    blocking_count: int
    warning_count: int


class DiagnosticResponse(BaseModel):
    run_id: str
    report_markdown: str
