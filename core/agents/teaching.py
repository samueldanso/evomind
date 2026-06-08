"""Teaching Agent — step function for the agent execution loop."""

from __future__ import annotations

from typing import Callable

from core.runtime.contracts import TeachTask


def run_teaching_agent(task: TeachTask, call_tool: Callable[[str, dict], dict]) -> dict:
    raise NotImplementedError("Teaching Agent not yet implemented — ships in T4")
