"""Tests for Phase D.1 — interactive teaching session, ingest CSS override, summary strip."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

import scripts.ingest as ingest
from core.governance.audit import (
    complete_run,
    create_run,
    get_run,
    pause_run,
    resume_run,
)
from core.tools.ingest import inject_light_css, LIGHT_OVERRIDE
from scripts.fix_summaries import clean_summary
from core.agents.teaching import run_teaching_turn
from core.runtime.contracts import TeachTask

MIGRATION_003 = Path("scripts/migrations/003_phase_d.sql").read_text()
MIGRATION_004 = Path("scripts/migrations/004_phase_d1.sql").read_text()


@pytest.fixture()
def db():
    conn = sqlite3.connect(":memory:")
    conn.executescript(MIGRATION_003)
    conn.execute("ALTER TABLE agent_runs ADD COLUMN session_log TEXT")
    yield conn
    conn.close()


class TestIngestLightCssInjection:
    def test_injects_after_head_tag(self):
        html = "<html><head><title>Test</title></head><body>Content</body></html>"
        result = inject_light_css(html)
        assert LIGHT_OVERRIDE in result
        assert result.index(LIGHT_OVERRIDE) > result.index("<head>")
        assert result.index(LIGHT_OVERRIDE) < result.index("<title>")

    def test_injects_after_head_with_attributes(self):
        html = '<html><head lang="en"><title>Test</title></head><body>Hi</body></html>'
        result = inject_light_css(html)
        assert LIGHT_OVERRIDE in result
        assert result.index(LIGHT_OVERRIDE) > result.index('<head lang="en">')

    def test_prepends_when_no_head(self):
        html = "<html><body>Content</body></html>"
        result = inject_light_css(html)
        assert result.startswith(LIGHT_OVERRIDE)

    def test_overrides_dark_css(self):
        html = (
            "<html><head><style>body{background:#1a1a1a;color:#e5e5e5;}</style></head>"
            "<body>Dark content</body></html>"
        )
        result = inject_light_css(html)
        assert "background:#fff!important" in result
        assert "color:#111!important" in result


class TestCleanSummary:
    def test_strips_html_tags(self):
        summary = "<p>This is a <strong>test</strong> summary</p>"
        result = clean_summary(summary)
        assert "<" not in result
        assert "This is a test summary" == result

    def test_strips_markdown_fences(self):
        summary = "```html\n<!DOCTYPE html><html><body>Hello</body></html>\n```"
        result = clean_summary(summary)
        assert "```" not in result
        assert "DOCTYPE" not in result

    def test_collapses_whitespace(self):
        summary = "  Multiple   spaces   and\nnewlines  "
        result = clean_summary(summary)
        assert "  " not in result
        assert "\n" not in result

    def test_truncates_long_summaries_at_sentence(self):
        summary = "First sentence. " * 30
        result = clean_summary(summary)
        assert len(result) <= 300
        assert result.endswith(".")

    def test_idempotent_on_clean_text(self):
        summary = "Already clean plain text summary."
        result = clean_summary(summary)
        assert result == summary


class TestAuditPauseResume:
    def test_pause_run_sets_status(self, db):
        run_id = create_run(db, "teaching_agent", {"topic": "Test"})
        pause_run(db, run_id, [{"role": "assistant", "content": "Hello"}])
        run = get_run(db, run_id)
        assert run["status"] == "paused_awaiting_input"

    def test_pause_run_stores_session_log(self, db):
        run_id = create_run(db, "teaching_agent", {"topic": "Test"})
        log = [{"role": "assistant", "content": "Opening"}, {"role": "user", "content": "Hi"}]
        pause_run(db, run_id, log)
        run = get_run(db, run_id)
        assert run["session_log"] == log

    def test_resume_run_sets_running(self, db):
        run_id = create_run(db, "teaching_agent", {"topic": "Test"})
        pause_run(db, run_id, [{"role": "assistant", "content": "Q"}])
        resume_run(db, run_id)
        run = get_run(db, run_id)
        assert run["status"] == "running"

    def test_get_run_includes_session_log(self, db):
        run_id = create_run(db, "teaching_agent", {"topic": "Test"})
        assert get_run(db, run_id).get("session_log") is None
        pause_run(db, run_id, [{"role": "assistant", "content": "Hi"}])
        run = get_run(db, run_id)
        assert run["session_log"] is not None
        assert len(run["session_log"]) == 1


class TestRunTeachingTurn:
    def _mock_call_tool(self, name, inp):
        if name == "retrieve":
            return {"results": []}
        elif name == "generate":
            return {"text": "Mock teaching response", "tokens_used": 10}
        elif name == "ingest":
            return {"artifact_id": 1, "slug": "test-mastery-checklist", "success": True}
        return {}

    def test_first_turn_returns_opening(self):
        task = TeachTask(task_type="teach", topic="KV Cache")
        result = run_teaching_turn(task, None, None, self._mock_call_tool)
        assert result["done"] is False
        assert result["phase"] == "opening"
        assert result["reply"] == "Mock teaching response"
        assert len(result["session_log"]) == 1
        assert result["session_log"][0]["role"] == "assistant"

    def test_subsequent_turn_advances(self):
        task = TeachTask(task_type="teach", topic="KV Cache")
        session_log = [{"role": "assistant", "content": "Opening"}]
        result = run_teaching_turn(task, "My answer", session_log, self._mock_call_tool)
        assert result["done"] is False
        assert result["phase"] == "layer"
        assert len(result["session_log"]) == 3

    def test_respects_max_turns(self):
        import os
        task = TeachTask(task_type="teach", topic="KV Cache")
        session_log = [{"role": "assistant", "content": f"Turn {i}"} for i in range(3)]
        os.environ["EVO_TEACH_MAX_TURNS"] = "3"
        try:
            result = run_teaching_turn(task, "Final answer", session_log, self._mock_call_tool)
            assert result["done"] is True
            assert result["phase"] == "checklist"
            assert "checklist_slug" in result
        finally:
            del os.environ["EVO_TEACH_MAX_TURNS"]
