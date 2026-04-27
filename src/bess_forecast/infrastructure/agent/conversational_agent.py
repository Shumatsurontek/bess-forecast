"""Conversational diagnostic agent.

Loads thread history from Postgres, replays it as LangChain messages, runs the
ReAct agent with `astream_events(version='v2')`, persists the new exchange, and
emits ProgressSink events so the front can stream the conversation in real time.
"""
from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langgraph.prebuilt import create_react_agent

from bess_forecast.domain.entities.agent import AgentMessage
from bess_forecast.domain.entities.progress_stage import AgentStage
from bess_forecast.domain.ports.agent_thread_repository import AgentThreadRepository
from bess_forecast.domain.ports.progress_sink import NoopProgressSink, ProgressSink
from bess_forecast.domain.services.prompts import DIAGNOSTIC_SYSTEM_PROMPT
from bess_forecast.infrastructure.agent.langsmith_config import merge_langsmith_config
from bess_forecast.infrastructure.agent.llm_factory import create_llm
from bess_forecast.infrastructure.agent.tools import ALL_TOOLS

logger = logging.getLogger(__name__)
AGENT_NAME = "forecast-diagnostic"


def _replay(messages: list[AgentMessage]) -> list:
    """Convert persisted messages into LangChain messages for re-injection."""
    out: list = []
    for m in messages:
        if m.role == "system":
            out.append(SystemMessage(content=m.content))
        elif m.role == "user":
            out.append(HumanMessage(content=m.content))
        elif m.role == "tool":
            out.append(ToolMessage(
                content=m.content,
                tool_call_id=(m.tool_args or {}).get("tool_call_id", "unknown"),
                name=m.tool_name or "tool",
            ))
        elif m.role == "assistant":
            tool_calls = []
            if m.tool_name:
                tool_calls.append({
                    "id": (m.tool_args or {}).get("tool_call_id", "call_" + m.id[:8]),
                    "name": m.tool_name,
                    "args": (m.tool_args or {}).get("args", {}),
                })
            out.append(AIMessage(content=m.content, tool_calls=tool_calls))
    return out


async def chat(
    *,
    thread_id: str,
    user_message: str,
    repo: AgentThreadRepository,
    progress: ProgressSink | None = None,
    site_id: str | None = None,
) -> str:
    """Run one user → assistant turn. Returns the final assistant content."""
    progress = progress or NoopProgressSink()

    history = repo.list_messages(thread_id)
    repo.add_message(thread_id, "user", user_message)

    # Pin the thread's forecast_run_id to the system prompt so the agent never
    # has to guess (or invent) which run it's diagnosing.
    thread = repo.get_thread(thread_id)
    system_prompt = DIAGNOSTIC_SYSTEM_PROMPT
    if thread and thread.forecast_run_id:
        system_prompt += (
            "\n\nCONTEXT FOR THIS THREAD:\n"
            f"- forecast_run_id = {thread.forecast_run_id}\n"
            "Use this exact run_id when calling get_forecast_run / "
            "compute_peak_metrics. Do NOT invent another id."
        )

    messages = [SystemMessage(content=system_prompt)]
    messages += _replay(history)
    messages.append(HumanMessage(content=user_message))

    llm = create_llm()
    agent = create_react_agent(model=llm, tools=ALL_TOOLS)

    config = merge_langsmith_config(
        {},
        run_id=thread_id,
        site_id=site_id,
        agent_name=AGENT_NAME,
        model_name=getattr(llm, "model_name", None) or getattr(llm, "model", None),
    )

    progress.emit(AgentStage.THINKING, "agent reasoning…")
    final_content = ""
    pending_tool_calls: dict[str, dict[str, Any]] = {}

    async for ev in agent.astream_events({"messages": messages}, config=config, version="v2"):
        kind = ev.get("event", "")
        name = ev.get("name", "")
        data = ev.get("data", {})

        if kind == "on_tool_start":
            tool_input = data.get("input", {})
            run_id = ev.get("run_id", "")
            pending_tool_calls[run_id] = {"name": name, "args": tool_input}
            progress.emit(
                AgentStage.TOOL_CALL,
                f"calling {name}",
                extra={"tool": name, "args": tool_input},
            )
        elif kind == "on_tool_end":
            run_id = ev.get("run_id", "")
            output = data.get("output")
            if hasattr(output, "content"):
                output_str = output.content if isinstance(output.content, str) else str(output.content)
            elif isinstance(output, str):
                output_str = output
            else:
                output_str = str(output)
            tool_info = pending_tool_calls.pop(run_id, {"name": name, "args": {}})
            repo.add_message(
                thread_id,
                "tool",
                output_str[:4000],
                tool_name=tool_info["name"],
                tool_args={"args": tool_info["args"], "tool_call_id": run_id},
            )
            progress.emit(
                AgentStage.TOOL_RESULT,
                f"{tool_info['name']} → {len(output_str)} chars",
                extra={"tool": tool_info["name"], "preview": output_str[:200]},
            )
        elif kind == "on_chat_model_end":
            output = data.get("output")
            if output is not None and getattr(output, "content", None):
                # Track the latest AIMessage content — we keep the last non-empty one,
                # which is the final assistant turn after all tool calls resolve.
                final_content = output.content if isinstance(output.content, str) else str(output.content)

    repo.add_message(thread_id, "assistant", final_content or "(no response)")
    repo.touch_thread(thread_id)
    progress.emit(AgentStage.FINAL_MESSAGE, "assistant replied",
                  extra={"content": final_content[:500]})
    progress.emit(AgentStage.DONE, "")
    return final_content
