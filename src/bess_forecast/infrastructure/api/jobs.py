"""In-process pub/sub for job progress events.

Jobs publish events; one or more WebSocket subscribers forward them to clients.
Single-process only — no Redis. Adequate for the demo (one uvicorn worker).
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from bess_forecast.domain.ports.progress_sink import ProgressSink

logger = logging.getLogger(__name__)

DONE_SENTINEL = {"__done__": True}


class JobBus:
    def __init__(self) -> None:
        self._queues: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}
        self._buffers: dict[str, list[dict[str, Any]]] = {}
        self._closed: set[str] = set()
        self._lock = asyncio.Lock()

    def new_job_id(self) -> str:
        return str(uuid.uuid4())

    async def subscribe(self, job_id: str) -> asyncio.Queue[dict[str, Any]]:
        async with self._lock:
            q: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
            self._queues.setdefault(job_id, []).append(q)
            # Replay any events that fired before the WS connected.
            for event in self._buffers.get(job_id, []):
                q.put_nowait(event)
            if job_id in self._closed:
                q.put_nowait(DONE_SENTINEL)
        return q

    def publish(self, job_id: str, event: dict[str, Any]) -> None:
        self._buffers.setdefault(job_id, []).append(event)
        for q in self._queues.get(job_id, []):
            q.put_nowait(event)

    def close(self, job_id: str) -> None:
        self._closed.add(job_id)
        for q in self._queues.get(job_id, []):
            q.put_nowait(DONE_SENTINEL)

    def buffer(self, job_id: str) -> list[dict[str, Any]]:
        return list(self._buffers.get(job_id, []))


bus = JobBus()


class JobBusProgressSink(ProgressSink):
    """Adapter from the domain `ProgressSink` port to the API-layer `JobBus`."""

    def __init__(self, bus: JobBus, job_id: str) -> None:
        self._bus = bus
        self._job_id = job_id

    def emit(
        self,
        stage: str,
        message: str = "",
        pct: float | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        evt = {"stage": stage, "message": message, "pct": pct, "extra": extra or {}}
        self._bus.publish(self._job_id, evt)
