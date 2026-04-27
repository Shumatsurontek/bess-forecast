"""Feature engineering for the LightGBM model.

Inputs: a tz-aware DatetimeIndex'd Series of kW (15-minute frequency).
Outputs: a DataFrame with lag/rolling/calendar features + the target column 'y'.
"""
from __future__ import annotations

import holidays
import pandas as pd

QUARTERS_PER_DAY = 96
QUARTERS_PER_WEEK = 7 * QUARTERS_PER_DAY


def build_features(
    s: pd.Series, *, holidays_years: tuple[int, ...] | None = None
) -> pd.DataFrame:
    """Build supervised-learning features. NaNs at the borders are kept; caller drops them."""
    if holidays_years is None:
        holidays_years = tuple({s.index.min().year, s.index.max().year})
    de_holidays = holidays.Germany(years=holidays_years)

    df = pd.DataFrame({"y": s.astype(float)}, index=s.index)
    df["lag_1"] = df["y"].shift(1)
    df["lag_96"] = df["y"].shift(QUARTERS_PER_DAY)
    df["lag_672"] = df["y"].shift(QUARTERS_PER_WEEK)
    df["roll_mean_4h"] = df["y"].shift(1).rolling(16).mean()
    df["roll_mean_24h"] = df["y"].shift(1).rolling(QUARTERS_PER_DAY).mean()

    idx = df.index
    df["hour"] = idx.hour.astype("int16")
    df["dayofweek"] = idx.dayofweek.astype("int16")
    df["month"] = idx.month.astype("int16")
    df["is_weekend"] = (idx.dayofweek >= 5).astype("int8")
    df["is_holiday_de"] = pd.Series(
        [d.date() in de_holidays for d in idx], index=idx
    ).astype("int8")
    return df


FEATURE_COLS = [
    "lag_1", "lag_96", "lag_672",
    "roll_mean_4h", "roll_mean_24h",
    "hour", "dayofweek", "month", "is_weekend", "is_holiday_de",
]
