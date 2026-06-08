"""Task dispatcher — validates, builds tool registry, chains Research → Teaching."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from core.memory.db import default_db_path
from core.runtime.contracts import AgentRun, ResearchTask, TeachTask, validate_task
from core.runtime.loop import run_agent
from core.tools.base import ToolRegistry
from core.tools.generate import build_generate_tool
from core.tools.ingest import build_ingest_tool
from core.tools.retrieve import build_retrieve_tool
from core.tools.web_search import build_web_search_tool


def _build_registry(db: sqlite3.Connection, provider, vault_path: Path) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(build_retrieve_tool(db, provider))
    registry.register(build_generate_tool(provider))
    registry.register(build_ingest_tool(db, vault_path))
    registry.register(build_web_search_tool())
    return registry


def dispatch(
    task: ResearchTask | TeachTask,
    db: sqlite3.Connection,
    provider,
    auto_teach: bool = True,
) -> AgentRun | tuple[AgentRun, AgentRun]:
    """Dispatch task to correct agent. If Research + auto_teach=True, chain Teaching after."""
    validate_task(task)

    vault_path = Path(os.environ.get("EVO_RESEARCH_STORE", str(default_db_path().parent)))
    registry = _build_registry(db, provider, vault_path)

    if isinstance(task, ResearchTask):
        tools = registry.build_for_agent("research_agent")
        research_run = run_agent("research_agent", task, tools, db)

        if auto_teach and research_run.status == "complete" and research_run.output:
            artifact_slug = research_run.output.get("artifact_slug")
            if artifact_slug:
                teach_task = TeachTask(
                    task_type="teach",
                    topic=task.topic,
                    artifact_slug=artifact_slug,
                )
                teach_tools = registry.build_for_agent("teaching_agent")
                teach_run = run_agent("teaching_agent", teach_task, teach_tools, db)
                return (research_run, teach_run)

        return research_run

    elif isinstance(task, TeachTask):
        tools = registry.build_for_agent("teaching_agent")
        return run_agent("teaching_agent", task, tools, db)

    else:
        msg = f"Unknown task type: {type(task)}"
        raise ValueError(msg)
