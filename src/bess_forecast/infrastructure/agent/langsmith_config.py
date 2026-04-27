"""Build / merge LangSmith metadata into a RunnableConfig.

Filterable tags: agent:<name>, model:<name>, site:<id>, run:<id>.
Filterable metadata: run_id, site_id, agent_name, model_name.
"""
from __future__ import annotations

from typing import Any

from langchain_core.runnables import RunnableConfig


def build_langsmith_config(
    *,
    run_id: str | None = None,
    site_id: str | None = None,
    agent_name: str | None = None,
    model_name: str | None = None,
    extra_tags: list[str] | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> RunnableConfig:
    metadata: dict[str, Any] = {}
    tags: list[str] = []
    if run_id:
        metadata["run_id"] = run_id
        tags.append(f"run:{run_id}")
    if site_id:
        metadata["site_id"] = site_id
        tags.append(f"site:{site_id}")
    if agent_name:
        metadata["agent_name"] = agent_name
        tags.append(f"agent:{agent_name}")
    if model_name:
        metadata["model_name"] = model_name
        tags.append(f"model:{model_name}")
    if extra_tags:
        tags.extend(extra_tags)
    if extra_metadata:
        metadata.update(extra_metadata)
    cfg: RunnableConfig = {"metadata": metadata}
    if tags:
        cfg["tags"] = tags
    if agent_name:
        cfg["run_name"] = f"diagnostic:{agent_name}"
    return cfg


def merge_langsmith_config(base: RunnableConfig, **kwargs: Any) -> RunnableConfig:
    ls = build_langsmith_config(**kwargs)
    merged: RunnableConfig = {**base, **ls}
    merged["metadata"] = {
        **dict(base.get("metadata") or {}),
        **dict(ls.get("metadata") or {}),
    }
    base_tags = base.get("tags") or []
    ls_tags = ls.get("tags") or []
    if base_tags or ls_tags:
        merged["tags"] = list(base_tags) + list(ls_tags)
    return merged
