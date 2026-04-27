"""TimesFM 2.5 zero-shot forecaster (google/timesfm-2.5-200m-transformers).

Optional dependency — install via `pip install bess_forecast[timesfm]`.
We import lazily so the rest of the package keeps working without torch.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from bess_forecast.domain.ports.model_port import ModelPort


class TimesFMZeroShot(ModelPort):
    name = "timesfm"
    version = "2.5-200m"

    def __init__(self, horizon: int = 96, context_length: int = 1024) -> None:
        self.horizon = horizon
        self.context_length = context_length
        self._history: np.ndarray | None = None
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            try:
                import torch
                from transformers import AutoModelForCausalLM
            except ImportError as e:
                raise ImportError(
                    "TimesFM requires the optional extra: "
                    "pip install 'bess_forecast[timesfm]'"
                ) from e
            self._torch = torch
            self._model = AutoModelForCausalLM.from_pretrained(
                "google/timesfm-2.5-200m-transformers",
                torch_dtype=torch.float32,
                trust_remote_code=True,
            ).eval()
        return self._model

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        self._history = y.tail(self.context_length).to_numpy(dtype=np.float32)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self._history is None:
            raise RuntimeError("Model not fitted")
        model = self._ensure_model()
        torch = self._torch
        with torch.no_grad():
            ctx = torch.tensor(self._history).unsqueeze(0)
            try:
                out = model.forecast(inputs=ctx, horizon=len(X))
            except AttributeError:
                # Fallback for HF generate-style decoder API.
                out = model.generate(ctx, max_new_tokens=len(X))
            arr = out.squeeze(0).cpu().numpy().astype(float)
        return arr[: len(X)]
