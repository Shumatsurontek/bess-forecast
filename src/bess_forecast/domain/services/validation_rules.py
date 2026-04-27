"""Pure validation rules — operate on a tz-aware DatetimeIndex'd Series of kW.

Each rule returns a list of ValidationIssue (possibly empty). No I/O here.
The expected sampling frequency is 15 minutes (Europe/Berlin).
"""
from __future__ import annotations

import pandas as pd

from bess_forecast.domain.entities.validation import Severity, ValidationIssue

EXPECTED_FREQ = pd.Timedelta(minutes=15)


def _sample(idx: pd.Index, n: int = 5) -> list[str]:
    return [str(x) for x in list(idx[:n])]


def check_temporal_continuity(s: pd.Series) -> list[ValidationIssue]:
    """No duplicates, monotonic, regular 15-minute step (DST gaps reported separately)."""
    issues: list[ValidationIssue] = []
    if not s.index.is_monotonic_increasing:
        issues.append(ValidationIssue(
            rule="temporal_continuity",
            severity=Severity.BLOCKING,
            message="Index is not monotonically increasing",
        ))
    dups = s.index[s.index.duplicated()]
    if len(dups) > 0:
        issues.append(ValidationIssue(
            rule="temporal_continuity",
            severity=Severity.BLOCKING,
            message=f"{len(dups)} duplicate timestamps",
            affected_count=int(len(dups)),
            sample=_sample(dups),
        ))
    if len(s) >= 2:
        deltas = s.index.to_series().diff().dropna()
        irregular = deltas[(deltas != EXPECTED_FREQ)]
        # We tolerate one positive deviation = DST jump (handled by check_dst_gaps).
        # Anything below EXPECTED_FREQ is irregular by definition.
        too_short = irregular[irregular < EXPECTED_FREQ]
        if len(too_short) > 0:
            issues.append(ValidationIssue(
                rule="temporal_continuity",
                severity=Severity.WARNING,
                message=f"{len(too_short)} sub-15min intervals",
                affected_count=int(len(too_short)),
                sample=_sample(too_short.index),
            ))
    return issues


def check_dst_gaps(s: pd.Series) -> list[ValidationIssue]:
    """Detect 1-hour gaps occurring at the last Sunday of March (spring-forward).

    These are expected if the upstream stores naive local times. We tag them
    as WARNING — the forecast can still proceed.
    """
    if len(s) < 2:
        return []
    idx = s.index
    deltas = idx.to_series().diff()
    # A spring-forward gap shows up as a single 1h15m delta (one missing 15m point)
    # repeated four times, or as a single 1h delta — both flagged here.
    gaps_1h_2h = deltas[(deltas > EXPECTED_FREQ) & (deltas <= pd.Timedelta(hours=2))]
    spring = [t for t in gaps_1h_2h.index if t.month == 3 and t.weekday() == 6]
    if not spring:
        return []
    return [ValidationIssue(
        rule="dst_gaps",
        severity=Severity.WARNING,
        message=f"{len(spring)} likely DST spring-forward gap(s)",
        affected_count=len(spring),
        sample=[str(t) for t in spring[:5]],
    )]


def check_physical_plausibility(s: pd.Series, max_kw: float) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    too_high = s[s > max_kw]
    if len(too_high) > 0:
        issues.append(ValidationIssue(
            rule="physical_plausibility",
            severity=Severity.BLOCKING,
            message=f"{len(too_high)} samples exceed asset max_kw={max_kw}",
            affected_count=int(len(too_high)),
            sample=_sample(too_high.index),
        ))
    negative = s[s < 0]
    if len(negative) > 0:
        issues.append(ValidationIssue(
            rule="physical_plausibility",
            severity=Severity.WARNING,
            message=f"{len(negative)} negative kW values (export?)",
            affected_count=int(len(negative)),
            sample=_sample(negative.index),
        ))
    return issues


def check_stuck_sensor(s: pd.Series, window: int = 8) -> list[ValidationIssue]:
    """Same exact value over `window` consecutive samples → likely frozen sensor."""
    if len(s) < window:
        return []
    same = (s == s.shift(1)).astype(int)
    # Run-length encoding via cumulative reset on changes.
    grp = (same != same.shift(1)).cumsum()
    runs = same.groupby(grp).transform("sum")
    stuck_idx = s.index[(same == 1) & (runs >= window - 1)]
    if len(stuck_idx) == 0:
        return []
    return [ValidationIssue(
        rule="stuck_sensor",
        severity=Severity.WARNING,
        message=f"{len(stuck_idx)} samples in stuck-value runs (window={window})",
        affected_count=int(len(stuck_idx)),
        sample=_sample(stuck_idx),
    )]


def check_outlier_zscore(s: pd.Series, z_threshold: float = 4.0,
                         window: str = "7D") -> list[ValidationIssue]:
    """Rolling z-score outliers (informational)."""
    if len(s) < 96:
        return []
    roll = s.rolling(window, min_periods=96)
    mu = roll.mean()
    sd = roll.std().replace(0, pd.NA)
    z = ((s - mu) / sd).abs()
    out = s[z > z_threshold]
    if len(out) == 0:
        return []
    return [ValidationIssue(
        rule="outlier_zscore",
        severity=Severity.WARNING,
        message=f"{len(out)} samples with |z| > {z_threshold}",
        affected_count=int(len(out)),
        sample=_sample(out.index),
    )]


def check_missing_ratio(s: pd.Series, max_ratio: float = 0.05) -> list[ValidationIssue]:
    """NaN ratio above threshold → block the run."""
    if len(s) == 0:
        return [ValidationIssue(
            rule="missing_ratio",
            severity=Severity.BLOCKING,
            message="Series is empty",
        )]
    ratio = float(s.isna().mean())
    if ratio > max_ratio:
        return [ValidationIssue(
            rule="missing_ratio",
            severity=Severity.BLOCKING,
            message=f"NaN ratio {ratio:.2%} exceeds max {max_ratio:.2%}",
            affected_count=int(s.isna().sum()),
        )]
    return []


def check_long_gap(s: pd.Series, max_minutes: int = 360) -> list[ValidationIssue]:
    """Continuous timestamp gap above `max_minutes` → block the run."""
    if len(s) < 2:
        return []
    deltas = s.index.to_series().diff()
    threshold = pd.Timedelta(minutes=max_minutes)
    big = deltas[deltas > threshold]
    if len(big) == 0:
        return []
    return [ValidationIssue(
        rule="long_gap",
        severity=Severity.BLOCKING,
        message=f"{len(big)} gap(s) longer than {max_minutes} minutes",
        affected_count=int(len(big)),
        sample=[str(t) for t in big.index[:5]],
    )]


ALL_RULES = (
    check_temporal_continuity,
    check_dst_gaps,
    check_stuck_sensor,
    check_outlier_zscore,
    check_missing_ratio,
    check_long_gap,
)
