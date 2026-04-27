"""LightGBM quantile regressor — primary production model.

Quantile alpha=0.75 biases predictions slightly upward, which fits the
peak-shaving asymmetry: missing a peak costs more than over-forecasting.
"""
from __future__ import annotations

import lightgbm as lgb
import numpy as np
import pandas as pd

from bess_forecast.application.services.feature_service import FEATURE_COLS
from bess_forecast.domain.ports.model_port import ModelPort


class LightGBMQuantile(ModelPort):
    name = "lightgbm_quantile"
    version = "1.0.0"

    def __init__(self, quantile: float = 0.75, n_estimators: int = 600,
                 learning_rate: float = 0.05, num_leaves: int = 63) -> None:
        self.quantile = quantile
        self._params = dict(
            objective="quantile",
            alpha=quantile,
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            num_leaves=num_leaves,
            min_data_in_leaf=50,
            verbose=-1,
        )
        self._model: lgb.LGBMRegressor | None = None

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        self._model = lgb.LGBMRegressor(**self._params)
        self._model.fit(X[FEATURE_COLS], y)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("Model not fitted")
        return self._model.predict(X[FEATURE_COLS])
