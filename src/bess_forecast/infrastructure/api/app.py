"""FastAPI app — exposes the pipeline so the React front can consume a stable schema."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bess_forecast.infrastructure.api.routers import diagnostic, forecast, telemetry, validation


def create_app() -> FastAPI:
    app = FastAPI(title="BESS Forecast", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(forecast.router)
    app.include_router(telemetry.router)
    app.include_router(diagnostic.router)
    app.include_router(validation.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
