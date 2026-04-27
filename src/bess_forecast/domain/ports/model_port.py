from abc import ABC, abstractmethod

import numpy as np
import pandas as pd


class ModelPort(ABC):
    """Single abstraction for naive / GBM / foundation-model backends."""

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> None: ...

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def version(self) -> str: ...
