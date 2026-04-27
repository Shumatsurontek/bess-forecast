"""Single source of truth for streamed pipeline / agent stages.

Exposed via the API schemas so `openapi-typescript-codegen` emits TS literal unions
on the frontend. Use these instead of hardcoding strings on either side.
"""
from enum import StrEnum


class ForecastStage(StrEnum):
    LOADING_CSV = "loading_csv"
    VALIDATING_RAW = "validating_raw"
    REPAIRING = "repairing"
    VALIDATING_POST = "validating_post"
    BUILDING_FEATURES = "building_features"
    FITTING = "fitting"
    PREDICTING = "predicting"
    COMPUTING_METRICS = "computing_metrics"
    SAVING = "saving"
    DONE = "done"
    ERROR = "error"


class AgentStage(StrEnum):
    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    FINAL_MESSAGE = "final_message"
    DONE = "done"
    ERROR = "error"
