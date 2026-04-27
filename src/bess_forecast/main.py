"""CLI entry-point: `python -m bess_forecast <command>`.

Commands:
    validate   — run validation rules on the CSV.
    run        — full forecast pipeline (load → validate → train → forecast → save).
    diagnose   — invoke the diagnostic agent on a forecast run.
    serve      — start the FastAPI app.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = typer.Typer(help="BESS short-term load forecast pipeline")

DEFAULT_CSV = Path("data/load_timeseries_2025_casestudy.csv")


@app.command()
def validate(
    csv: Path = typer.Option(DEFAULT_CSV, exists=True, readable=True),
    max_kw: float = typer.Option(200.0, help="Asset rated max kW"),
) -> None:
    """Run validation rules on the CSV and print the report."""
    from bess_forecast.application.services.validation_service import validate as run
    from bess_forecast.infrastructure.persistence.csv_telemetry_repository import load_csv

    s = load_csv(csv)
    report = run(s, max_kw=max_kw)
    typer.echo(f"Issues: {len(report.issues)} "
               f"(blocking={report.blocking_count}, warning={report.warning_count})")
    for issue in report.issues:
        typer.echo(f"  [{issue.severity.value}] {issue.rule}: {issue.message}")
    raise typer.Exit(code=1 if report.is_blocking else 0)


@app.command()
def run(
    csv: Path = typer.Option(DEFAULT_CSV, exists=True, readable=True),
    asof: str = typer.Option(..., help="ISO datetime, e.g. 2025-12-01T00:00:00"),
    model: str = typer.Option("lgbm", help="naive | lgbm | timesfm"),
    site: str = typer.Option(os.getenv("SITE_NAME", "default")),
    asset: str = typer.Option(os.getenv("ASSET_NAME", "meter-01")),
    max_kw: float = typer.Option(float(os.getenv("ASSET_MAX_KW", "200.0"))),
    quantile: float = typer.Option(float(os.getenv("QUANTILE", "0.75"))),
    plots: bool = typer.Option(True, help="Save the 3 README figures"),
    out_dir: Path = typer.Option(Path("outputs")),
) -> None:
    """Full pipeline. Saves forecast (parquet + JSONL) and figures to outputs/."""
    from bess_forecast.application.use_cases.run_forecast import run_forecast
    from bess_forecast.infrastructure.persistence.csv_telemetry_repository import load_csv
    from bess_forecast.infrastructure.persistence.inmemory_forecast_repository import (
        InMemoryForecastRepository,
    )

    asof_dt = datetime.fromisoformat(asof)
    repo = InMemoryForecastRepository()
    result = run_forecast(
        csv_path=csv, site_id=site, asset_id=asset, asof=asof_dt,
        model_name=model, asset_max_kw=max_kw, quantile=quantile,
        forecast_repo=repo,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "figures").mkdir(exist_ok=True)
    (out_dir / "reports").mkdir(exist_ok=True)

    pq = out_dir / f"forecast_{result.run.id}.parquet"
    import pandas as pd
    pd.DataFrame(
        [{"ts": p.ts, "kw_pred": p.kw_pred} for p in result.points]
    ).to_parquet(pq, index=False)

    repo.dump_jsonl(out_dir / f"forecast_{result.run.id}.jsonl")
    (out_dir / f"metrics_{result.run.id}.json").write_text(
        json.dumps(result.metrics, indent=2, default=str)
    )

    if plots:
        from bess_forecast.visualization.plots import (
            daily_profile, forecast_vs_actual, heatmap_hour_dow,
        )
        s = load_csv(csv)
        daily_profile(s, out_dir / "figures" / "daily_profile.png")
        heatmap_hour_dow(s, out_dir / "figures" / "heatmap_hour_dow.png")
        actual = s.loc[
            (s.index >= result.run.horizon_start) & (s.index <= result.run.horizon_end)
        ]
        forecast_vs_actual(
            actual, result.points,
            float(result.metrics["threshold_kw"]),
            out_dir / "figures" / f"forecast_vs_actual_{result.run.id}.png",
        )

    typer.echo(f"Run id : {result.run.id}")
    typer.echo(f"Model  : {result.run.model_name} v{result.run.model_version}")
    typer.echo(f"Metrics: {json.dumps(result.metrics, indent=2, default=str)}")


@app.command()
def diagnose(
    run_id: Optional[str] = typer.Option(None, help="Run ID (omit to run forecast first)"),
    csv: Path = typer.Option(DEFAULT_CSV, exists=True, readable=True),
    asof: str = typer.Option("2025-12-01T00:00:00"),
    model: str = typer.Option("lgbm"),
    out: Path = typer.Option(Path("outputs/reports")),
) -> None:
    """Invoke the diagnostic agent. If --run-id is omitted, runs a forecast first."""
    from bess_forecast.application.use_cases.run_forecast import run_forecast
    from bess_forecast.infrastructure.agent.tools import configure_tools
    from bess_forecast.infrastructure.persistence.holidays_calendar_repository import (
        HolidaysCalendarRepository,
    )
    from bess_forecast.infrastructure.persistence.inmemory_forecast_repository import (
        InMemoryForecastRepository,
    )
    from bess_forecast.infrastructure.persistence.csv_telemetry_repository import (
        CsvTelemetryRepository,
    )

    site = os.getenv("SITE_NAME", "default")
    asset = os.getenv("ASSET_NAME", "meter-01")
    forecast_repo = InMemoryForecastRepository()
    telemetry_repo = CsvTelemetryRepository(csv, site_id=site, asset_id=asset)

    if run_id is None:
        result = run_forecast(
            csv_path=csv, site_id=site, asset_id=asset,
            asof=datetime.fromisoformat(asof), model_name=model,
            forecast_repo=forecast_repo,
        )
        run_id = result.run.id
        typer.echo(f"Forecast run created: {run_id}")

    configure_tools(
        forecast_repo=forecast_repo,
        telemetry_repo=telemetry_repo,
        calendar_repo=HolidaysCalendarRepository(),
    )
    from bess_forecast.application.use_cases.run_diagnostic import run_diagnostic
    report = run_diagnostic(run_id, site_id=site)

    out.mkdir(parents=True, exist_ok=True)
    path = out / f"diagnostic_{run_id}.md"
    path.write_text(report)
    typer.echo(f"Report → {path}")
    typer.echo("\n" + report)


@app.command()
def serve(
    host: str = typer.Option(os.getenv("API_HOST", "0.0.0.0")),
    port: int = typer.Option(int(os.getenv("API_PORT", "8000"))),
    reload: bool = typer.Option(False),
) -> None:
    """Start the FastAPI app."""
    import uvicorn
    uvicorn.run("bess_forecast.infrastructure.api.app:app",
                host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
