# BESS Short-Term Load Forecast

A small production-shaped pipeline that forecasts 15-minute load for a Commercial &
Industrial site running a Battery Energy Storage System. The forecast feeds a
peak-shaving controller, so errors have **asymmetric costs**: a missed peak is
billed in demand charges, an over-forecast burns battery cycles. This drives
every design choice below.

## What's in here

```
src/bess_forecast/      # Python package (clean architecture)
  domain/               # entities, ports, validation rules, prompts
  application/          # services + use cases (orchestration)
  infrastructure/       # CSV/Postgres repos, models, FastAPI, agent
  visualization/        # 3 figures for the README
alembic/                # versioned DB migrations (Postgres)
tests/                  # validation rules + agent mocked E2E
frontend/               # Vite + React + TS, openapi codegen
data/                   # input CSV (gitignored)
outputs/                # forecasts, figures, diagnostic reports
```

## Quickstart

```bash
# 1. Python deps + dev tools
just setup                    # uv sync + pytest

# 2. Run the dev stack (postgres + adminer + log viewer + api + front)
cp .env.example .env          # then put your real OPENAI_API_KEY inside
just dev                      # spawns docker, applies alembic, starts API + Vite
```

After `just dev`:

| URL | What |
|---|---|
| http://localhost:5173 | React app (forecast, validation, chat) |
| http://localhost:8000/health | FastAPI health |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8080 | **Dozzle** — live container logs (incl. tailed API log) |
| http://localhost:8081 | **Adminer** — Postgres SQL browser |

Run a forecast from the UI, or by CLI:

```bash
just run-lgbm            # asof = 2025-07-15, peaks captured ≈ 15/15 vs naive 0/15
just compare             # naive vs lgbm side-by-side
uv run pytest            # 20 tests
```

### LLM / agent

The diagnostic agent uses LangChain `ChatOpenAI` directly. Set the standard
OpenAI env vars in `.env`:

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini       # any model your key has access to
LANGSMITH_TRACING=true         # optional — traces every tool call
LANGSMITH_API_KEY=lsv2_...
LANGCHAIN_PROJECT=bess-forecast
```

In the `/chat` page, click **+ New chat**: a thread is created bound to the
most-recent forecast run, and the agent can answer questions about it (4
read-only tools: get_forecast_run, get_actuals, compute_peak_metrics,
get_calendar_context). Tool calls and assistant replies are persisted in
`agent_threads` / `agent_messages` and visible in Adminer.

Live progress for both the forecast pipeline and the agent streams over
`/ws/jobs/{job_id}` (typed events, see `domain/entities/progress_stage.py`).

## Part 1 — Validation

Rules are pure functions in
[`src/bess_forecast/domain/services/validation_rules.py`](src/bess_forecast/domain/services/validation_rules.py)
classified by severity:

| Rule                     | Severity | What it catches                                      |
|--------------------------|----------|------------------------------------------------------|
| `temporal_continuity`    | BLOCKING | non-monotonic / duplicate timestamps                 |
| `dst_gaps`               | WARNING  | spring-forward 1h gap on the last March Sunday       |
| `physical_plausibility`  | BLOCK/WARN | values above asset rated max ; negatives = export |
| `stuck_sensor`           | WARNING  | identical value on ≥ 8 consecutive quarter-hours     |
| `outlier_zscore`         | WARNING  | rolling 7-day z-score > 4                            |
| `missing_ratio`          | BLOCKING | NaN ratio > 5 % over the training horizon            |
| `long_gap`               | BLOCKING | continuous gap > 6 h (can't ffill safely)            |

**Blocking → run aborted, fallback to last forecast.**
**Warning → tagged with `quality_flag`, run continues.**

Tests in [`tests/test_validation_rules.py`](tests/test_validation_rules.py)
cover one path per rule plus edge cases (DST, all-NaN, empty series).

## Part 2 — Forecast

### Modeling choice — why pinball loss

The peak-shaving controller cares about **whether the forecast crosses the
threshold**, not about RMSE. We optimize a quantile loss with `α = 0.75` so
the model leans slightly upward in uncertain regions — fewer missed peaks,
some intentional over-forecasting.

### Three providers behind one `ModelPort`

| Backend              | Role                                                       |
|----------------------|------------------------------------------------------------|
| `NaiveBaseline`      | Floor — same quarter-of-hour, one week ago (lag-672).      |
| `LightGBMQuantile`   | **Primary**. Lag/rolling/calendar features, `α=0.75`.      |
| `TimesFMZeroShot`    | Optional. Google's foundation model `google/timesfm-2.5-200m-transformers` — zero-shot, no training. |

CLI flag: `--model {naive,lgbm,timesfm}`.

### Features used by LightGBM
[`feature_service.py`](src/bess_forecast/application/services/feature_service.py):
lag-1, lag-96 (1 day), lag-672 (1 week), rolling means 4 h / 24 h, hour,
dayofweek, month, is_weekend, is_holiday_de (German public holidays via
the `holidays` package).

### Metrics
[`metrics_service.py`](src/bess_forecast/application/services/metrics_service.py):

- **Pinball loss** (`α=0.75`) — primary.
- RMSE / MAE — informative.
- **Peak Capture Rate** — share of actuals ≥ threshold that the forecast
  also placed ≥ threshold. Threshold = 85 % of `max(actual)` over the
  horizon (operating point of the controller).
- **Incidents** — list of (ts, predicted, actual, gap) for each missed
  peak or significant over-forecast.

### Output

`outputs/forecast_<run_id>.parquet` (target ts + kw_pred), a metrics JSON,
and 3 figures generated in `outputs/figures/`:

1. Daily profile (median + IQR by hour)
2. Heatmap hour × day of week
3. Forecast vs actual with the peak threshold

## Part 3 — Postgres schema

Versioned via Alembic
([`alembic/versions/`](alembic/versions/)).

### Why this shape

- **Bi-temporal**: `forecast_runs.generated_at` is the *as-of* of the run.
  The query "what did the forecast say at time T?" is
  `ORDER BY generated_at DESC LIMIT 1 WHERE generated_at <= T` — O(log n)
  thanks to the `(site_id, generated_at DESC)` index.
- **Telemetry partitioned monthly** on `ts`. Retention deletes drop a
  partition (instant) instead of scanning the whole table. Inserts hit a
  small partition.
- **Runs split from points**: one `forecast_runs` row holds metadata
  (model, version, quantile, metrics JSONB), `forecast_points` only carries
  `(ts, kw_pred)`. Comparing models is a JOIN on `forecast_runs`.
- `quality_flag SMALLINT` on telemetry traces interpolated / suspect rows
  end-to-end.
- `UNIQUE (site_id, generated_at, model_version, quantile)` makes retries
  idempotent.

```
sites          (id, name, timezone)
assets         (id, site_id, name, max_kw)
telemetry_15m  (site_id, asset_id, ts PK, kw, quality_flag, ingested_at)
                 PARTITION BY RANGE (ts) — monthly
forecast_runs  (id, site_id, generated_at, horizon_*, model_*, quantile, metrics JSONB)
forecast_points(run_id, ts PK, kw_pred)  ON DELETE CASCADE
```

## Diagnostic agent (read-only, hors path critique)

[`run_diagnostic.py`](src/bess_forecast/application/use_cases/run_diagnostic.py)
wraps a small LangChain ReAct agent with **four read-only tools** bound to
the domain ports:

- `get_forecast_run(run_id)`
- `get_actuals(site_id, since, until)`
- `compute_peak_metrics_tool(run_id, threshold_kw)`
- `get_calendar_context(date)`

System prompt
([`prompts.py`](src/bess_forecast/domain/services/prompts.py)) constrains
the agent to a fixed Markdown layout (Summary / Incidents table / Root
cause / Suggested action) and forbids any production-affecting suggestion.

LangSmith config in
[`langsmith_config.py`](src/bess_forecast/infrastructure/agent/langsmith_config.py)
attaches `run_id`, `site_id`, `agent_name`, `model_name` as metadata + tags
— filterable in the LangSmith UI, replayable.

The agent is **never in the decision path**. It explains, doesn't act.

## Frontend

Vite + React + TypeScript. The OpenAPI client is **generated** from the
running FastAPI app:

```bash
cd frontend
npm install
npm run generate:api    # writes src/api/ from /openapi.json
npm run dev
```

A thin [`repositories/`](frontend/src/repositories/) layer wraps the
generated client so UI code stays stable when the API evolves. The visual
language is inspired by 3blue1brown — dark navy, teal/yellow accents,
serif headings, monospace numerics, framer-motion reveals.

## Decisions, in one table

| Sujet                 | Choix                                              |
|-----------------------|----------------------------------------------------|
| Loss                  | Pinball, α = 0.75 (peak-asymmetric)                |
| Baseline obligatoire  | Naive lag-672                                      |
| Primary model         | LightGBM quantile                                  |
| FM backend            | TimesFM 2.5 (zero-shot, optional)                  |
| Migrations            | Alembic                                            |
| Tests                 | pytest — validation rules + 1 mocked agent E2E     |
| Agent                 | Read-only, structured prompt, LangSmith tagged     |
| Frontend client       | Generated from OpenAPI                             |
