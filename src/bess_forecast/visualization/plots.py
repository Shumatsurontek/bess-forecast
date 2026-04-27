"""Three figures for the README.

1. Daily profile (median + p25/p75 by hour).
2. Heatmap hour x dayofweek.
3. Forecast vs actual on a window with the peak threshold.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from bess_forecast.domain.entities.forecast import ForecastPoint


def daily_profile(s: pd.Series, out_path: str | Path) -> None:
    df = pd.DataFrame({"kw": s.values, "hour": s.index.hour})
    grp = df.groupby("hour")["kw"]
    p50 = grp.median()
    p25 = grp.quantile(0.25)
    p75 = grp.quantile(0.75)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.fill_between(p50.index, p25, p75, alpha=0.25, label="p25–p75")
    ax.plot(p50.index, p50, lw=2, label="median")
    ax.set_xlabel("hour of day")
    ax.set_ylabel("kW")
    ax.set_title("Daily load profile (median, IQR)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def heatmap_hour_dow(s: pd.Series, out_path: str | Path) -> None:
    df = pd.DataFrame({"kw": s.values, "h": s.index.hour, "dow": s.index.dayofweek})
    mat = df.groupby(["dow", "h"])["kw"].mean().unstack("h")
    fig, ax = plt.subplots(figsize=(9, 3.5))
    im = ax.imshow(mat.values, aspect="auto", cmap="viridis")
    ax.set_yticks(range(7))
    ax.set_yticklabels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    ax.set_xlabel("hour")
    ax.set_title("Mean kW by hour × day of week")
    fig.colorbar(im, ax=ax, label="kW")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def forecast_vs_actual(
    actual: pd.Series, points: list[ForecastPoint],
    threshold_kw: float, out_path: str | Path
) -> None:
    pred = pd.Series(
        {p.ts: p.kw_pred for p in points}, name="forecast"
    ).sort_index()
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(actual.index, actual.values, lw=1.5, label="actual", color="#0d2538")
    ax.plot(pred.index, pred.values, lw=1.5, label="forecast", color="#5cd9c1")
    ax.axhline(threshold_kw, ls="--", color="#ffe066", label=f"peak threshold ({threshold_kw:.0f} kW)")
    ax.set_ylabel("kW")
    ax.set_title("Forecast vs actual")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
