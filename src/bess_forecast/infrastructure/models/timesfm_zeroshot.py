"""TimesFM 2.5 zero-shot forecaster (google/timesfm-2.5-200m-transformers).

Optional dependency — install via `uv pip install -e '.[timesfm]'`.
The model is loaded lazily so the rest of the package keeps working without torch.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from bess_forecast.domain.ports.model_port import ModelPort

logger = logging.getLogger(__name__)


class TimesFMZeroShot(ModelPort):
    name = "timesfm"
    version = "2.5-200m"

    def __init__(self, horizon: int = 96, context_length: int = 1024) -> None:
        self.horizon = horizon
        self.context_length = context_length
        self._history: np.ndarray | None = None
        self._model = None
        self._torch = None

    def _ensure_model(self):
        if self._model is None:
            try:
                import torch
                from transformers import TimesFm2_5ModelForPrediction
            except ImportError as e:
                raise ImportError(
                    "TimesFM requires the optional extra: "
                    "uv pip install -e '.[timesfm]'"
                ) from e
            self._torch = torch
            logger.info("Loading google/timesfm-2.5-200m-transformers")
            self._model = TimesFm2_5ModelForPrediction.from_pretrained(
                "google/timesfm-2.5-200m-transformers",
                dtype=torch.float32,
            ).eval()
        return self._model

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        # Zero-shot — we just stash the recent context.
        self._history = y.tail(self.context_length).to_numpy(dtype=np.float32)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self._history is None:
            raise RuntimeError("Model not fitted")
        model = self._ensure_model()
        torch = self._torch
        ctx = torch.from_numpy(self._history).float()
        with torch.no_grad():
            out = model([ctx])
        # `mean_predictions` is shape (batch=1, model_horizon=128).
        preds = out.mean_predictions[0].cpu().numpy().astype(float)
        n = len(X)
        if n <= len(preds):
            return preds[:n]
        # Asked for a horizon longer than the model produces — pad with last value.
        pad = np.full(n - len(preds), preds[-1], dtype=float)
        return np.concatenate([preds, pad])
