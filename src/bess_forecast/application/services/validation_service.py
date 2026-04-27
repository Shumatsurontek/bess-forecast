"""Aggregates rules into a single ValidationReport."""
from __future__ import annotations

import pandas as pd

from bess_forecast.domain.entities.validation import ValidationReport
from bess_forecast.domain.services.validation_rules import (
    check_long_gap,
    check_missing_ratio,
    check_outlier_zscore,
    check_physical_plausibility,
    check_stuck_sensor,
    check_temporal_continuity,
    check_dst_gaps,
)


def validate(s: pd.Series, *, max_kw: float) -> ValidationReport:
    """Run the full rule set on a kW Series."""
    issues = []
    issues += check_temporal_continuity(s)
    issues += check_dst_gaps(s)
    issues += check_physical_plausibility(s, max_kw=max_kw)
    issues += check_stuck_sensor(s)
    issues += check_outlier_zscore(s)
    issues += check_missing_ratio(s)
    issues += check_long_gap(s)
    return ValidationReport(issues=issues)
