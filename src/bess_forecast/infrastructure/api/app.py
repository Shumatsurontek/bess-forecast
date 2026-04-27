"""FastAPI app — exposes the pipeline so the React front can consume a stable schema."""
from __future__ import annotations

import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from bess_forecast.infrastructure.api.middleware import AccessLogMiddleware
from bess_forecast.infrastructure.api.routers import (
    diagnostic,
    forecast,
    jobs,
    telemetry,
    threads,
    validation,
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="BESS Forecast", version="0.2.0")

    # CORS first so error responses still carry the headers.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Access log second so it sees the response status after CORS rewrites.
    app.add_middleware(AccessLogMiddleware, database_url=os.getenv("DATABASE_URL"))

    app.include_router(forecast.router)
    app.include_router(telemetry.router)
    app.include_router(diagnostic.router)
    app.include_router(validation.router)
    app.include_router(jobs.router)
    app.include_router(threads.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.exception_handler(Exception)
    async def all_errors(request: Request, exc: Exception):
        # Critical: returning a JSONResponse routes back through CORSMiddleware,
        # so the browser sees a real 500 with CORS headers (not a CORS error).
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "type": exc.__class__.__name__},
        )

    return app


app = create_app()
