# BESS Forecast — task runner
# Usage: `just <recipe>`. List recipes: `just`.

set dotenv-load := true

CSV := "data/load_timeseries_2025_casestudy.csv"
ASOF := "2025-07-15T00:00:00"
MAX_KW := "1000"

# Default — show all recipes
default:
    @just --list

# ---- Setup ---------------------------------------------------------------

# Sync python deps and install dev extras (pytest etc.)
setup:
    uv sync
    uv pip install pytest pytest-mock

# Optional TimesFM extra (downloads ~800MB on first inference)
setup-timesfm:
    uv pip install -e ".[timesfm]"

# Frontend deps
setup-frontend:
    cd frontend && npm install

# Bootstrap a fresh .env from the example
env:
    test -f .env || cp .env.example .env
    @echo ".env ready — edit it for OpenAI / LangSmith keys"

# ---- Quality -------------------------------------------------------------

# Run the test suite
test:
    uv run pytest -v

# Validate the case-study CSV
validate:
    uv run python -m bess_forecast validate --csv {{CSV}} --max-kw {{MAX_KW}}

# ---- Pipeline ------------------------------------------------------------

# Run the forecast pipeline (default: lgbm, 2025-07-15)
run model="lgbm" asof=ASOF:
    uv run python -m bess_forecast run \
        --csv {{CSV}} --asof {{asof}} --model {{model}} --max-kw {{MAX_KW}}

# Naive baseline (the floor every model must beat)
run-naive asof=ASOF:
    @just run naive {{asof}}

# LightGBM (primary)
run-lgbm asof=ASOF:
    @just run lgbm {{asof}}

# TimesFM zero-shot (requires `just setup-timesfm`)
run-timesfm asof=ASOF:
    @just run timesfm {{asof}}

# Run all three models on the same as-of and compare
compare asof=ASOF:
    @just run-naive {{asof}}
    @just run-lgbm {{asof}}

# Diagnostic agent — runs a forecast + invokes the LLM
diagnose asof=ASOF:
    uv run python -m bess_forecast diagnose --csv {{CSV}} --asof {{asof}}

# ---- Database ------------------------------------------------------------

# Start postgres + adminer
db-up:
    docker compose up -d
    @echo "Adminer at http://localhost:8080"

db-down:
    docker compose down

# Apply alembic migrations
db-migrate:
    uv run alembic upgrade head

# Rollback all migrations
db-rollback:
    uv run alembic downgrade base

# ---- API + Frontend ------------------------------------------------------

# Start the FastAPI app (reload mode)
serve:
    uv run python -m bess_forecast serve --reload

# Generate the typed API client from the running FastAPI app
gen-client:
    cd frontend && npm run generate:api

# Start the React dev server
frontend:
    cd frontend && npm run dev

# Full local dev stack: db + api in background, frontend in foreground
dev:
    @just db-up
    @just db-migrate
    uv run python -m bess_forecast serve --reload &
    @sleep 2
    @just gen-client
    @just frontend

# ---- Cleanup -------------------------------------------------------------

clean:
    rm -rf outputs/*.parquet outputs/*.json outputs/*.jsonl
    rm -rf outputs/figures/* outputs/reports/*
    rm -rf .pytest_cache .ruff_cache .mypy_cache

clean-all: clean
    rm -rf .venv frontend/node_modules frontend/dist frontend/openapi.json frontend/src/api
