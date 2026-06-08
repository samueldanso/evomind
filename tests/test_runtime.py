"""Tests for core/runtime/loop.py — agent execution loop."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from core.runtime.contracts import ResearchTask, TeachTask
from core.runtime.loop import run_agent
from core.tools.base import Tool

MIGRATION_SQL = Path("scripts/migrations/003_phase_d.sql").read_text()


@pytest.fixture()
def db():
    conn = sqlite3.connect(":memory:")
    conn.executescript(MIGRATION_SQL)
    yield conn
    conn.close()


def _mock_tool(name: str, output: dict | None = None) -> Tool:
    return Tool(
        name=name,
        description=f"Mock {name}",
        execute=lambda inp: output or {"tokens_used": 0, "cost_usd": 0.0},
    )


def _generate_tool(tokens: int = 100) -> Tool:
    return Tool(
        name="generate",
        description="Mock generate",
        execute=lambda inp: {"text": "response", "tokens_used": tokens, "cost_usd": 0.0},
    )


def _failing_tool(name: str, error_msg: str = "boom") -> Tool:
    def execute(inp):
        raise RuntimeError(error_msg)

    return Tool(name=name, description=f"Failing {name}", execute=execute)


class TestRunAgentComplete:
    def test_run_agent_complete(self, db):
        def mock_research(task, call_tool):
            call_tool("retrieve", {"query": "test"})
            call_tool("generate", {"messages": [{"role": "user", "content": "test"}]})
            return {"artifact_slug": "test-slug"}

        tools = {
            "retrieve": _mock_tool("retrieve", {"results": [], "tokens_used": 0}),
            "generate": _generate_tool(50),
            "ingest": _mock_tool("ingest"),
        }

        with patch("core.agents.research.run_research_agent", mock_research):
            result = run_agent("research_agent", ResearchTask(task_type="research", topic="Test", mode="concept"), tools, db)

        assert result.status == "complete"
        assert result.output == {"artifact_slug": "test-slug"}
        assert result.id is not None

    def test_run_agent_tool_calls_recorded(self, db):
        def mock_research(task, call_tool):
            call_tool("retrieve", {"query": "KV Cache"})
            call_tool("generate", {"messages": [{"role": "user", "content": "write"}]})
            return {"done": True}

        tools = {
            "retrieve": _mock_tool("retrieve", {"results": [], "tokens_used": 0}),
            "generate": _generate_tool(25),
            "ingest": _mock_tool("ingest"),
        }

        with patch("core.agents.research.run_research_agent", mock_research):
            result = run_agent("research_agent", ResearchTask(task_type="research", topic="KV Cache", mode="concept"), tools, db)

        assert len(result.tool_calls) == 2
        assert result.tool_calls[0].tool_name == "retrieve"
        assert result.tool_calls[1].tool_name == "generate"

    def test_run_agent_cost_accumulates(self, db):
        def mock_research(task, call_tool):
            call_tool("generate", {"messages": [{"role": "user", "content": "a"}]})
            call_tool("generate", {"messages": [{"role": "user", "content": "b"}]})
            return {"done": True}

        tools = {
            "retrieve": _mock_tool("retrieve"),
            "generate": _generate_tool(100),
            "ingest": _mock_tool("ingest"),
        }

        with patch("core.agents.research.run_research_agent", mock_research):
            result = run_agent("research_agent", ResearchTask(task_type="research", topic="Cost", mode="concept"), tools, db)

        assert result.cost_tokens == 200


class TestRunAgentFailure:
    def test_run_agent_tool_raises_marks_failed(self, db):
        def mock_research(task, call_tool):
            call_tool("retrieve", {"query": "test"})
            return {"done": True}

        tools = {
            "retrieve": _failing_tool("retrieve", "connection timeout"),
            "generate": _generate_tool(),
            "ingest": _mock_tool("ingest"),
        }

        with patch("core.agents.research.run_research_agent", mock_research):
            result = run_agent("research_agent", ResearchTask(task_type="research", topic="Fail", mode="concept"), tools, db)

        assert result.status == "failed"
        assert "connection timeout" in result.error

    def test_run_agent_partial_log_on_failure(self, db):
        call_count = [0]

        def mock_research(task, call_tool):
            call_tool("retrieve", {"query": "ok"})
            call_tool("generate", {"messages": [{"role": "user", "content": "fail"}]})
            return {"done": True}

        def retrieve_exec(inp):
            return {"results": [], "tokens_used": 0}

        def generate_exec(inp):
            raise RuntimeError("provider error")

        tools = {
            "retrieve": Tool(name="retrieve", description="ok", execute=retrieve_exec),
            "generate": Tool(name="generate", description="fail", execute=generate_exec),
            "ingest": _mock_tool("ingest"),
        }

        with patch("core.agents.research.run_research_agent", mock_research):
            result = run_agent("research_agent", ResearchTask(task_type="research", topic="Partial", mode="concept"), tools, db)

        assert result.status == "failed"
        assert len(result.tool_calls) == 2
        assert result.tool_calls[0].success is True
        assert result.tool_calls[1].success is False

    def test_run_agent_allowlist_violation(self, db):
        def mock_research(task, call_tool):
            call_tool("web_search", {"query": "not allowed"})
            return {"done": True}

        tools = {
            "retrieve": _mock_tool("retrieve"),
            "generate": _generate_tool(),
            "ingest": _mock_tool("ingest"),
            "web_search": _mock_tool("web_search"),
        }

        with patch("core.agents.research.run_research_agent", mock_research):
            result = run_agent("research_agent", ResearchTask(task_type="research", topic="Blocked", mode="concept"), tools, db)

        assert result.status == "failed"
        assert "not allowed" in result.error or "PermissionError" in result.error
