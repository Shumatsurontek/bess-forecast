"""CSV telemetry source for the case-study file.

Format: `Timestamps;Load_kw` with German conventions (semicolon separator,
comma decimal, DD.MM.YYYY HH:MM dates). Naive local time → localized to
Europe/Berlin (`ambiguous='infer', nonexistent='shift_forward'`).
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from bess_forecast.domain.entities.telemetry import TelemetryReading
from bess_forecast.domain.ports.telemetry_repository import TelemetryRepository


def load_csv(path: str | Path, tz: str = "Europe/Berlin") -> pd.Series:
    """Return a tz-aware Series indexed by timestamp, named 'kw'."""
    df = pd.read_csv(path, sep=";", decimal=",", dtype={"Load_kw": float})
    ts = pd.to_datetime(df["Timestamps"], format="%d.%m.%Y %H:%M", errors="raise")
    s = pd.Series(df["Load_kw"].to_numpy(), index=ts, name="kw")
    s = s.sort_index()
    # Fall-back DST creates one ambiguous hour per year; treat it as winter time
    # (the second, post-shift occurrence). Spring-forward gaps are shifted forward.
    s.index = s.index.tz_localize(
        tz, ambiguous=False, nonexistent="shift_forward"
    )
    return s


class CsvTelemetryRepository(TelemetryRepository):
    """Read-only telemetry source backed by a single CSV file."""

    def __init__(self, path: str | Path, site_id: str, asset_id: str) -> None:
        self._path = Path(path)
        self._site_id = site_id
        self._asset_id = asset_id
        self._series: pd.Series | None = None

    def _load(self) -> pd.Series:
        if self._series is None:
            self._series = load_csv(self._path)
        return self._series

    def load(
        self, site_id: str, since: datetime, until: datetime
    ) -> list[TelemetryReading]:
        if site_id != self._site_id:
            return []
        s = self._load()
        # Make `since` / `until` tz-aware in the same tz as the index.
        tz = s.index.tz
        since_tz = since if since.tzinfo else pd.Timestamp(since).tz_localize(tz)
        until_tz = until if until.tzinfo else pd.Timestamp(until).tz_localize(tz)
        sub = s.loc[(s.index >= since_tz) & (s.index <= until_tz)]
        return [
            TelemetryReading(self._site_id, self._asset_id, ts.to_pydatetime(), float(v))
            for ts, v in sub.items()
        ]

    def save_many(self, readings: list[TelemetryReading]) -> int:
        raise NotImplementedError("CSV repository is read-only")

    def as_series(self) -> pd.Series:
        return self._load()
