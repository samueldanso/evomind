"""Typed task contracts for the agent runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

VALID_RESEARCH_MODES = ("concept", "tool", "company")


@dataclass
class ResearchTask:
    task_type: Literal["research"]
    topic: str
    mode: Literal["concept", "tool", "company"]
    context: str | None = None


@dataclass
class TeachTask:
    task_type: Literal["teach"]
    topic: str
    artifact_slug: str | None = None
    mastery_context: str | None = None


@dataclass
class ToolCallRecord:
    tool_name: str
    input: dict
    output: dict
    success: bool
    error: str | None
    tokens_used: int
    called_at: str


@dataclass
class AgentRun:
    id: int | None
    agent_type: str
    task_input: dict
    status: Literal["running", "complete", "failed"]
    output: dict | None
    error: str | None
    tool_calls: list[ToolCallRecord]
    cost_tokens: int
    cost_usd: float
    started_at: str
    finished_at: str | None


def validate_task(task: ResearchTask | TeachTask) -> None:
    """Validate a task contract. Raises ValueError on invalid input."""
    if isinstance(task, ResearchTask):
        if task.task_type != "research":
            msg = f"ResearchTask.task_type must be 'research', got '{task.task_type}'"
            raise ValueError(msg)
        if not task.topic or not task.topic.strip():
            msg = "ResearchTask.topic must be a non-empty string"
            raise ValueError(msg)
        if task.mode not in VALID_RESEARCH_MODES:
            msg = f"ResearchTask.mode must be one of {VALID_RESEARCH_MODES}, got '{task.mode}'"
            raise ValueError(msg)
    elif isinstance(task, TeachTask):
        if task.task_type != "teach":
            msg = f"TeachTask.task_type must be 'teach', got '{task.task_type}'"
            raise ValueError(msg)
        if not task.topic or not task.topic.strip():
            msg = "TeachTask.topic must be a non-empty string"
            raise ValueError(msg)
    else:
        msg = f"Unknown task type: {type(task).__name__}"
        raise ValueError(msg)
