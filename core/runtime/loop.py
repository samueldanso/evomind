"""Agent execution loop — dispatches agent step functions and records all tool calls."""

from __future__ import annotations

import dataclasses
import sqlite3
from datetime import UTC, datetime

from core.governance import audit
from core.governance.allowlist import check_allowlist
from core.runtime.contracts import AgentRun, ResearchTask, TeachTask, ToolCallRecord
from core.tools.base import Tool


def run_agent(
    agent_type: str,
    task: ResearchTask | TeachTask,
    tools: dict[str, Tool],
    db: sqlite3.Connection,
) -> AgentRun:
    """Execute an agent step function to completion. Returns the completed AgentRun."""
    run_id = audit.create_run(db, agent_type, dataclasses.asdict(task))

    cost_tokens = 0
    cost_usd = 0.0
    tool_calls_log: list[ToolCallRecord] = []

    def call_tool(tool_name: str, tool_input: dict) -> dict:
        nonlocal cost_tokens, cost_usd
        check_allowlist(agent_type, tool_name)
        if tool_name not in tools:
            msg = f"Tool {tool_name!r} not registered for agent {agent_type!r}"
            raise KeyError(msg)

        tool = tools[tool_name]
        called_at = datetime.now(UTC).isoformat()
        try:
            output = tool.execute(tool_input)
            tokens = output.get("tokens_used", 0)
            usd = output.get("cost_usd", 0.0)
            cost_tokens += tokens
            cost_usd += usd
            record = ToolCallRecord(
                tool_name=tool_name,
                input=tool_input,
                output=output,
                success=True,
                error=None,
                tokens_used=tokens,
                called_at=called_at,
            )
            audit.record_tool_call(db, run_id, record)
            tool_calls_log.append(record)
            return output
        except Exception as exc:
            record = ToolCallRecord(
                tool_name=tool_name,
                input=tool_input,
                output={},
                success=False,
                error=str(exc),
                tokens_used=0,
                called_at=called_at,
            )
            audit.record_tool_call(db, run_id, record)
            tool_calls_log.append(record)
            raise

    try:
        from core.agents.research import run_research_agent
        from core.agents.teaching import run_teaching_agent

        if agent_type == "research_agent":
            output = run_research_agent(task, call_tool)
        elif agent_type == "teaching_agent":
            output = run_teaching_agent(task, call_tool)
        else:
            msg = f"Unknown agent_type: {agent_type!r}"
            raise ValueError(msg)

        audit.complete_run(db, run_id, output, cost_tokens, cost_usd)
        run_data = audit.get_run(db, run_id)

        return AgentRun(
            id=run_id,
            agent_type=agent_type,
            task_input=dataclasses.asdict(task),
            status="complete",
            output=output,
            error=None,
            tool_calls=tool_calls_log,
            cost_tokens=cost_tokens,
            cost_usd=cost_usd,
            started_at=run_data["started_at"] if run_data else "",
            finished_at=run_data["finished_at"] if run_data else "",
        )
    except Exception as exc:
        audit.fail_run(db, run_id, str(exc), cost_tokens, cost_usd)
        run_data = audit.get_run(db, run_id)

        return AgentRun(
            id=run_id,
            agent_type=agent_type,
            task_input=dataclasses.asdict(task),
            status="failed",
            output=None,
            error=str(exc),
            tool_calls=tool_calls_log,
            cost_tokens=cost_tokens,
            cost_usd=cost_usd,
            started_at=run_data["started_at"] if run_data else "",
            finished_at=run_data["finished_at"] if run_data else "",
        )
