"""Forecast Diagnostic Agent — explains forecast vs actual gaps post-hoc."""
from __future__ import annotations

from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from bess_forecast.domain.services.prompts import DIAGNOSTIC_SYSTEM_PROMPT
from bess_forecast.infrastructure.agent.langsmith_config import merge_langsmith_config
from bess_forecast.infrastructure.agent.llm_factory import create_llm
from bess_forecast.infrastructure.agent.tools import ALL_TOOLS

AGENT_NAME = "forecast-diagnostic"


def build_agent():
    return create_react_agent(
        model=create_llm(),
        tools=ALL_TOOLS,
        state_modifier=DIAGNOSTIC_SYSTEM_PROMPT,
    )


def run_diagnostic(run_id: str, *, site_id: str | None = None) -> str:
    agent = build_agent()
    llm = create_llm()
    config = merge_langsmith_config(
        {},
        run_id=run_id,
        site_id=site_id,
        agent_name=AGENT_NAME,
        model_name=getattr(llm, "model_name", None) or getattr(llm, "model", None),
    )
    out = agent.invoke(
        {"messages": [HumanMessage(
            content=f"Diagnose forecast run with run_id={run_id}. "
                    "Use the tools to gather data, then produce the Markdown report."
        )]},
        config=config,
    )
    return out["messages"][-1].content
