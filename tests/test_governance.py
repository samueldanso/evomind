"""Tests for core/governance/ — allowlist enforcement and audit logging."""

import sqlite3
from pathlib import Path

import pytest

from core.governance.allowlist import check_allowlist
from core.governance.audit import (
    complete_run,
    create_run,
    fail_run,
    get_run,
    list_runs,
    record_tool_call,
)
from core.runtime.contracts import ToolCallRecord

MIGRATION_SQL = Path("scripts/migrations/003_phase_d.sql").read_text()


@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    conn.executescript(MIGRATION_SQL)
    yield conn
    conn.close()


class TestAllowlist:
    def test_allowlist_research_retrieve(self):
        check_allowlist("research_agent", "retrieve")

    def test_allowlist_research_generate(self):
        check_allowlist("research_agent", "generate")

    def test_allowlist_research_ingest(self):
        check_allowlist("research_agent", "ingest")

    def test_allowlist_blocks_web_search(self):
        with pytest.raises(PermissionError, match="not allowed"):
            check_allowlist("research_agent", "web_search")

    def test_allowlist_unknown_agent(self):
        with pytest.raises(PermissionError, match="Unknown agent type"):
            check_allowlist("unknown_agent", "retrieve")


class TestAudit:
    def test_create_run_returns_int(self, db):
        run_id = create_run(db, "research_agent", {"topic": "KV Cache"})
        assert isinstance(run_id, int)

    def test_record_tool_call_appends(self, db):
        run_id = create_run(db, "research_agent", {"topic": "KV Cache"})
        record = ToolCallRecord(
            tool_name="retrieve",
            input={"query": "KV Cache"},
            output={"results": []},
            success=True,
            error=None,
            tokens_used=0,
            called_at="2026-06-07T00:00:00Z",
        )
        record_tool_call(db, run_id, record)
        run = get_run(db, run_id)
        assert run is not None
        assert len(run["tool_calls"]) == 1
        assert run["tool_calls"][0]["tool_name"] == "retrieve"

    def test_complete_run_updates_status(self, db):
        run_id = create_run(db, "research_agent", {"topic": "KV Cache"})
        complete_run(db, run_id, {"artifact_slug": "kv-cache"}, cost_tokens=1500, cost_usd=0.003)
        run = get_run(db, run_id)
        assert run is not None
        assert run["status"] == "complete"
        assert run["finished_at"] is not None
        assert run["cost_tokens"] == 1500
        assert run["cost_usd"] == 0.003

    def test_fail_run_records_error(self, db):
        run_id = create_run(db, "research_agent", {"topic": "KV Cache"})
        fail_run(db, run_id, "Provider timeout", cost_tokens=500, cost_usd=0.001)
        run = get_run(db, run_id)
        assert run is not None
        assert run["status"] == "failed"
        assert run["error"] == "Provider timeout"
        assert run["finished_at"] is not None

    def test_get_run_correct_shape(self, db):
        run_id = create_run(db, "teaching_agent", {"topic": "Transformers"})
        run = get_run(db, run_id)
        assert run is not None
        expected_keys = {
            "id", "agent_type", "task_input", "status", "output",
            "error", "tool_calls", "cost_tokens", "cost_usd",
            "started_at", "finished_at",
        }
        assert set(run.keys()) == expected_keys

    def test_list_runs_respects_limit(self, db):
        for i in range(5):
            create_run(db, "research_agent", {"topic": f"Topic {i}"})
        runs = list_runs(db, limit=3)
        assert len(runs) == 3
