"""Research Agent — step function for the agent execution loop."""

from __future__ import annotations

from typing import Callable

from core.runtime.contracts import ResearchTask


def run_research_agent(task: ResearchTask, call_tool: Callable[[str, dict], dict]) -> dict:
    raise NotImplementedError("Research Agent not yet implemented — ships in T4")
