"""Postgres-backed agent thread/message repository."""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from bess_forecast.domain.entities.agent import AgentMessage, AgentThread
from bess_forecast.domain.ports.agent_thread_repository import AgentThreadRepository


def _dump_json(value: Any) -> str | None:
    return json.dumps(value) if value is not None else None


class PostgresAgentRepository(AgentThreadRepository):
    def __init__(self, url: str) -> None:
        self._engine: Engine = create_engine(url, future=True)

    # ---- threads ----
    def create_thread(
        self, title: str, forecast_run_id: str | None = None
    ) -> AgentThread:
        sql = text("""
            INSERT INTO agent_threads (title, forecast_run_id)
            VALUES (:title, :run_id)
            RETURNING id::text, title, forecast_run_id::text, created_at, updated_at
        """)
        with self._engine.begin() as conn:
            row = conn.execute(sql, {"title": title, "run_id": forecast_run_id}).one()
        return AgentThread(
            id=row[0], title=row[1], forecast_run_id=row[2],
            created_at=row[3], updated_at=row[4],
        )

    def get_thread(self, thread_id: str) -> AgentThread | None:
        sql = text("""
            SELECT id::text, title, forecast_run_id::text, created_at, updated_at
            FROM agent_threads WHERE id = :id
        """)
        with self._engine.connect() as conn:
            row = conn.execute(sql, {"id": thread_id}).first()
        if not row:
            return None
        return AgentThread(
            id=row[0], title=row[1], forecast_run_id=row[2],
            created_at=row[3], updated_at=row[4],
        )

    def list_threads(self, limit: int = 50) -> list[AgentThread]:
        sql = text("""
            SELECT id::text, title, forecast_run_id::text, created_at, updated_at
            FROM agent_threads ORDER BY updated_at DESC LIMIT :lim
        """)
        with self._engine.connect() as conn:
            rows = conn.execute(sql, {"lim": limit}).all()
        return [
            AgentThread(id=r[0], title=r[1], forecast_run_id=r[2],
                        created_at=r[3], updated_at=r[4])
            for r in rows
        ]

    def touch_thread(self, thread_id: str) -> None:
        sql = text("UPDATE agent_threads SET updated_at = now() WHERE id = :id")
        with self._engine.begin() as conn:
            conn.execute(sql, {"id": thread_id})

    # ---- messages ----
    def add_message(
        self,
        thread_id: str,
        role: str,
        content: str,
        *,
        tool_name: str | None = None,
        tool_args: dict[str, Any] | None = None,
        tool_result: dict[str, Any] | None = None,
        tokens: int | None = None,
    ) -> AgentMessage:
        sql = text("""
            INSERT INTO agent_messages
                (thread_id, role, content, tool_name, tool_args, tool_result, tokens)
            VALUES (:tid, :role, :content, :tn,
                    CAST(:ta AS JSONB), CAST(:tr AS JSONB), :tk)
            RETURNING id::text, thread_id::text, role, content, tool_name,
                      tool_args, tool_result, tokens, created_at
        """)
        with self._engine.begin() as conn:
            row = conn.execute(sql, {
                "tid": thread_id, "role": role, "content": content,
                "tn": tool_name, "ta": _dump_json(tool_args),
                "tr": _dump_json(tool_result), "tk": tokens,
            }).one()
        return AgentMessage(
            id=row[0], thread_id=row[1], role=row[2], content=row[3],
            tool_name=row[4], tool_args=row[5], tool_result=row[6],
            tokens=row[7], created_at=row[8],
        )

    def list_messages(self, thread_id: str) -> list[AgentMessage]:
        sql = text("""
            SELECT id::text, thread_id::text, role, content, tool_name,
                   tool_args, tool_result, tokens, created_at
            FROM agent_messages WHERE thread_id = :tid
            ORDER BY created_at ASC
        """)
        with self._engine.connect() as conn:
            rows = conn.execute(sql, {"tid": thread_id}).all()
        return [
            AgentMessage(
                id=r[0], thread_id=r[1], role=r[2], content=r[3],
                tool_name=r[4], tool_args=r[5], tool_result=r[6],
                tokens=r[7], created_at=r[8],
            )
            for r in rows
        ]
