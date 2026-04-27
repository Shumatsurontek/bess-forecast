from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from bess_forecast.domain.entities.validation import Severity
from bess_forecast.domain.services.validation_rules import (
    check_long_gap,
    check_missing_ratio,
    check_outlier_zscore,
    check_physical_plausibility,
    check_stuck_sensor,
    check_temporal_continuity,
)


def _series(n: int = 96, start: str = "2025-06-01", value: float = 50.0) -> pd.Series:
    idx = pd.date_range(start, periods=n, freq="15min", tz="Europe/Berlin")
    return pd.Series([value] * n, index=idx, name="kw")


def test_temporal_continuity_clean_series_no_issues():
    assert check_temporal_continuity(_series()) == []


def test_temporal_continuity_detects_duplicates():
    s = _series(10)
    s = pd.concat([s, s.iloc[[0]]])
    issues = check_temporal_continuity(s)
    assert any(i.severity == Severity.BLOCKING and "duplicate" in i.message
               for i in issues)


def test_temporal_continuity_detects_non_monotonic():
    s = _series(10)
    s = s.iloc[::-1]
    assert any(i.severity == Severity.BLOCKING for i in check_temporal_continuity(s))


def test_physical_plausibility_flags_above_max():
    s = _series(10)
    s.iloc[3] = 999.0
    issues = check_physical_plausibility(s, max_kw=200.0)
    assert any(i.rule == "physical_plausibility" and i.severity == Severity.BLOCKING
               for i in issues)


def test_physical_plausibility_negative_warns():
    s = _series(10)
    s.iloc[1] = -3.0
    issues = check_physical_plausibility(s, max_kw=200.0)
    assert any(i.severity == Severity.WARNING and "negative" in i.message for i in issues)


def test_stuck_sensor_detects_constant_run():
    s = _series(20, value=10.0)
    issues = check_stuck_sensor(s, window=8)
    assert len(issues) == 1
    assert issues[0].severity == Severity.WARNING


def test_stuck_sensor_ignores_short_run():
    s = _series(20, value=10.0)
    s.iloc[5:15] = np.linspace(1, 10, 10)  # break the run
    issues = check_stuck_sensor(s, window=8)
    # Remaining stuck windows at the borders shorter than 8 — must report none.
    # (Tail is 5 stuck, head is 5 stuck — both below window.)
    assert issues == []


def test_outlier_zscore_flags_spike():
    s = _series(7 * 96 * 2, value=50.0)
    s = s + np.random.default_rng(0).normal(0, 1, len(s))
    s.iloc[-1] = 1000.0
    issues = check_outlier_zscore(s, z_threshold=4.0)
    assert len(issues) == 1


def test_missing_ratio_blocks_when_above_threshold():
    s = _series(100, value=10.0)
    s.iloc[:20] = np.nan
    issues = check_missing_ratio(s, max_ratio=0.05)
    assert any(i.severity == Severity.BLOCKING for i in issues)


def test_missing_ratio_passes_when_below_threshold():
    s = _series(100, value=10.0)
    s.iloc[:1] = np.nan
    assert check_missing_ratio(s, max_ratio=0.05) == []


def test_missing_ratio_empty_series_blocks():
    s = pd.Series([], dtype=float, index=pd.DatetimeIndex([], tz="Europe/Berlin"))
    issues = check_missing_ratio(s)
    assert issues and issues[0].severity == Severity.BLOCKING


def test_long_gap_blocks():
    idx = pd.DatetimeIndex(
        ["2025-01-01 00:00", "2025-01-01 00:15", "2025-01-01 10:00"],
        tz="Europe/Berlin",
    )
    s = pd.Series([1.0, 2.0, 3.0], index=idx)
    issues = check_long_gap(s, max_minutes=360)
    assert issues and issues[0].severity == Severity.BLOCKING


def test_long_gap_no_issue_within_threshold():
    idx = pd.date_range("2025-01-01", periods=10, freq="15min", tz="Europe/Berlin")
    s = pd.Series(range(10), index=idx, dtype=float)
    assert check_long_gap(s, max_minutes=360) == []
