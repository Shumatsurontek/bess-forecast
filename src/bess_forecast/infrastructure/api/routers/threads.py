"""Conversational agent threads — list / create / read messages / chat."""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from bess_forecast.infrastructure.agent.tools import configure_tools
from bess_forecast.infrastructure.api import state
from bess_forecast.infrastructure.api.jobs import JobBusProgressSink, bus
from bess_forecast.infrastructure.api.schemas import (
    AgentMessageDTO,
    AgentThreadDTO,
    JobAcceptedDTO,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/threads", tags=["threads"])


class CreateThreadRequest(BaseModel):
    forecast_run_id: str | None = None
    title: str | None = None


class SendMessageRequest(BaseModel):
    content: str


def _to_thread_dto(t) -> AgentThreadDTO:
    return AgentThreadDTO(
        id=t.id, title=t.title, forecast_run_id=t.forecast_run_id,
        created_at=t.created_at, updated_at=t.updated_at,
    )


def _to_msg_dto(m) -> AgentMessageDTO:
    return AgentMessageDTO(
        id=m.id, thread_id=m.thread_id, role=m.role, content=m.content,
        tool_name=m.tool_name, tool_args=m.tool_args, tool_result=m.tool_result,
        tokens=m.tokens, created_at=m.created_at,
    )


@router.post("", response_model=AgentThreadDTO)
def create_thread(req: CreateThreadRequest) -> AgentThreadDTO:
    if state.agent_repo is None:
        raise HTTPException(503, "Agent thread persistence requires DATABASE_URL")
    title = req.title
    if not title and req.forecast_run_id:
        title = f"Diagnostic for run {req.forecast_run_id[:8]}"
    title = title or "New conversation"
    t = state.agent_repo.create_thread(title=title, forecast_run_id=req.forecast_run_id)
    return _to_thread_dto(t)


@router.get("", response_model=list[AgentThreadDTO])
def list_threads(limit: int = 50) -> list[AgentThreadDTO]:
    if state.agent_repo is None:
        return []
    return [_to_thread_dto(t) for t in state.agent_repo.list_threads(limit=limit)]


@router.get("/{thread_id}/messages", response_model=list[AgentMessageDTO])
def list_messages(thread_id: str) -> list[AgentMessageDTO]:
    if state.agent_repo is None:
        raise HTTPException(503, "Agent persistence not available")
    return [_to_msg_dto(m) for m in state.agent_repo.list_messages(thread_id)]


@router.post("/{thread_id}/messages", response_model=JobAcceptedDTO)
def send_message(
    thread_id: str, req: SendMessageRequest, tasks: BackgroundTasks
) -> JobAcceptedDTO:
    if state.agent_repo is None:
        raise HTTPException(503, "Agent persistence not available")
    if state.agent_repo.get_thread(thread_id) is None:
        raise HTTPException(404, f"Thread {thread_id} not found")

    job_id = bus.new_job_id()
    sink = JobBusProgressSink(bus, job_id)
    configure_tools(
        forecast_repo=state.forecast_repo,
        telemetry_repo=state.telemetry_repo,
        calendar_repo=state.calendar_repo,
    )

    async def _run() -> None:
        from bess_forecast.infrastructure.agent.conversational_agent import chat
        try:
            await chat(
                thread_id=thread_id,
                user_message=req.content,
                repo=state.agent_repo,
                progress=sink,
                site_id=str(state.SITE_ID),
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Agent chat failed")
            sink.emit("error", str(exc))
        finally:
            bus.close(job_id)

    tasks.add_task(asyncio.create_task, _run())
    return JobAcceptedDTO(job_id=job_id)
