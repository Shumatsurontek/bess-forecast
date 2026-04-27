from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class AgentThread:
    id: str
    title: str
    forecast_run_id: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class AgentMessage:
    id: str
    thread_id: str
    role: str  # 'user' | 'assistant' | 'tool' | 'system'
    content: str
    created_at: datetime
    tool_name: str | None = None
    tool_args: dict[str, Any] | None = None
    tool_result: dict[str, Any] | None = None
    tokens: int | None = None
