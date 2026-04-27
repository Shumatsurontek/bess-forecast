from abc import ABC, abstractmethod
from typing import Any

from bess_forecast.domain.entities.agent import AgentMessage, AgentThread


class AgentThreadRepository(ABC):
    @abstractmethod
    def create_thread(
        self, title: str, forecast_run_id: str | None = None
    ) -> AgentThread: ...

    @abstractmethod
    def get_thread(self, thread_id: str) -> AgentThread | None: ...

    @abstractmethod
    def list_threads(self, limit: int = 50) -> list[AgentThread]: ...

    @abstractmethod
    def touch_thread(self, thread_id: str) -> None: ...

    @abstractmethod
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
    ) -> AgentMessage: ...

    @abstractmethod
    def list_messages(self, thread_id: str) -> list[AgentMessage]: ...
