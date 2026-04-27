"""WebSocket job-progress endpoint + JSON poll fallback."""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from bess_forecast.infrastructure.api.jobs import DONE_SENTINEL, bus

router = APIRouter(tags=["jobs"])


@router.websocket("/ws/jobs/{job_id}")
async def job_stream(ws: WebSocket, job_id: str) -> None:
    await ws.accept()
    queue = await bus.subscribe(job_id)
    try:
        while True:
            event = await queue.get()
            if event is DONE_SENTINEL:
                await ws.send_text(json.dumps({"stage": "__done__"}))
                break
            await ws.send_text(json.dumps(event, default=str))
    except WebSocketDisconnect:
        return
    except asyncio.CancelledError:
        return
    finally:
        try:
            await ws.close()
        except RuntimeError:
            pass


@router.get("/jobs/{job_id}")
def get_job_events(job_id: str) -> dict:
    """Poll fallback — returns the buffered events so far."""
    return {"job_id": job_id, "events": bus.buffer(job_id)}
