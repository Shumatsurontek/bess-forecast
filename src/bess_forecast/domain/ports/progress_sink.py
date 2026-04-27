"""Port for streaming pipeline / agent progress events.

Use cases stay pure: they take a `ProgressSink` and call `emit(stage, ...)` at key
boundaries. The infrastructure layer wires a concrete sink (JobBus over WS, or a
no-op for tests / CLI).
"""
from __future__ import annotations

from typing import Any, Protocol


class ProgressSink(Protocol):
    def emit(
        self,
        stage: str,
        message: str = "",
        pct: float | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None: ...


class NoopProgressSink:
    def emit(
        self,
        stage: str,
        message: str = "",
        pct: float | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        return None
