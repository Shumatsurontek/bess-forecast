"""Naive baseline: same-quarter-of-hour, one week ago (lag-672).

This is the floor every other model must beat. The case study explicitly
accepts this baseline.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from bess_forecast.application.services.feature_service import QUARTERS_PER_WEEK
from bess_forecast.domain.ports.model_port import ModelPort


class NaiveBaseline(ModelPort):
    name = "naive_lag672"
    version = "1.0.0"

    def __init__(self) -> None:
        self._history: pd.Series | None = None

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        self._history = y.copy()

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self._history is None:
            raise RuntimeError("Model not fitted")
        offset = pd.Timedelta(minutes=15) * QUARTERS_PER_WEEK
        lookup = X.index - offset
        h = self._history
        # If the as-of is far in the future and the lookup falls past the end of
        # the history, rotate back by 52-week chunks to land inside (= same week
        # of the most-recent calendar year available).
        year = pd.Timedelta(weeks=52)
        while lookup.max() > h.index.max():
            lookup = lookup - year
        return h.reindex(lookup).ffill().bfill().to_numpy(dtype=float)
