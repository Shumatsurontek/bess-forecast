from __future__ import annotations

from fastapi import APIRouter

from bess_forecast.application.services.validation_service import validate
from bess_forecast.infrastructure.api import state
from bess_forecast.infrastructure.api.schemas import (
    ValidationIssueDTO,
    ValidationReportDTO,
)

router = APIRouter(prefix="/validation", tags=["validation"])


@router.get("/last", response_model=ValidationReportDTO)
def validate_last() -> ValidationReportDTO:
    s = state.telemetry_repo.as_series()
    report = validate(s, max_kw=state.ASSET_MAX_KW)
    return ValidationReportDTO(
        issues=[
            ValidationIssueDTO(
                rule=i.rule, severity=i.severity.value, message=i.message,
                affected_count=i.affected_count, sample=i.sample,
            )
            for i in report.issues
        ],
        blocking_count=report.blocking_count,
        warning_count=report.warning_count,
    )
