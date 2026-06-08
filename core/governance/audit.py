"""Agent run audit logging and cost tracking."""

from __future__ import annotations

import dataclasses
import json
import sqlite3
from datetime import datetime, timezone

from core.runtime.contracts import ToolCallRecord


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def create_run(db: sqlite3.Connection, agent_type: str, task_input: dict) -> int:
    """Insert a new agent_runs row with status='running'. Returns run_id."""
    cursor = db.execute(
        """INSERT INTO agent_runs (agent_type, task_input, status, started_at)
           VALUES (?, ?, 'running', ?)""",
        (agent_type, json.dumps(task_input), _utc_now()),
    )
    db.commit()
    return cursor.lastrowid  # type: ignore[return-value]


def record_tool_call(db: sqlite3.Connection, run_id: int, record: ToolCallRecord) -> None:
    """Atomically append a tool call record to the run's tool_calls JSON array."""
    record_json = json.dumps(dataclasses.asdict(record))
    db.execute(
        "UPDATE agent_runs SET tool_calls = json_insert(tool_calls, '$[#]', json(?)) WHERE id = ?",
        (record_json, run_id),
    )
    db.commit()


def complete_run(
    db: sqlite3.Connection, run_id: int, output: dict, cost_tokens: int, cost_usd: float
) -> None:
    """Mark a run as complete with output and cost data."""
    db.execute(
        """UPDATE agent_runs
           SET status = 'complete', output = ?, cost_tokens = ?, cost_usd = ?, finished_at = ?
           WHERE id = ?""",
        (json.dumps(output), cost_tokens, cost_usd, _utc_now(), run_id),
    )
    db.commit()


def fail_run(
    db: sqlite3.Connection, run_id: int, error: str, cost_tokens: int, cost_usd: float
) -> None:
    """Mark a run as failed with error and cost data."""
    db.execute(
        """UPDATE agent_runs
           SET status = 'failed', error = ?, cost_tokens = ?, cost_usd = ?, finished_at = ?
           WHERE id = ?""",
        (error, cost_tokens, cost_usd, _utc_now(), run_id),
    )
    db.commit()


def pause_run(db: sqlite3.Connection, run_id: int, session_log: list[dict]) -> None:
    """Pause a teaching run awaiting user input."""
    db.execute(
        "UPDATE agent_runs SET status = 'paused_awaiting_input', session_log = ? WHERE id = ?",
        (json.dumps(session_log), run_id),
    )
    db.commit()


def resume_run(db: sqlite3.Connection, run_id: int) -> None:
    """Resume a paused run back to running status."""
    db.execute(
        "UPDATE agent_runs SET status = 'running' WHERE id = ?",
        (run_id,),
    )
    db.commit()


def get_run(db: sqlite3.Connection, run_id: int) -> dict | None:
    """Fetch a single run by ID. Returns dict or None if not found."""
    db.row_factory = sqlite3.Row
    row = db.execute("SELECT * FROM agent_runs WHERE id = ?", (run_id,)).fetchone()
    if row is None:
        return None
    result = dict(row)
    result["tool_calls"] = json.loads(result["tool_calls"])
    if result["output"]:
        result["output"] = json.loads(result["output"])
    if result["task_input"]:
        result["task_input"] = json.loads(result["task_input"])
    if result.get("session_log"):
        result["session_log"] = json.loads(result["session_log"])
    return result


def list_runs(db: sqlite3.Connection, limit: int = 20) -> list[dict]:
    """Fetch the most recent runs, ordered by ID descending."""
    db.row_factory = sqlite3.Row
    rows = db.execute(
        "SELECT * FROM agent_runs ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    results = []
    for row in rows:
        r = dict(row)
        r["tool_calls"] = json.loads(r["tool_calls"])
        if r["output"]:
            r["output"] = json.loads(r["output"])
        if r["task_input"]:
            r["task_input"] = json.loads(r["task_input"])
        if r.get("session_log"):
            r["session_log"] = json.loads(r["session_log"])
        results.append(r)
    return results
