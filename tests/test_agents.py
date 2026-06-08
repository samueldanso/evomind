"""Tests for core/agents/ and core/runtime/dispatcher.py."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

import scripts.ingest as ingest
from core.llm.bedrock import ChatResponse
from core.runtime.contracts import AgentRun, ResearchTask, TeachTask
from core.runtime.dispatcher import dispatch


class MockProvider:
    def embed(self, texts: list[str], input_type: str = "search_document") -> list[list[float]]:
        return [[0.1] * 1024 for _ in texts]

    def chat(self, messages, context_chunks):
        return ChatResponse(content="mock agent response", citations=[])


MIGRATION_003 = Path("scripts/migrations/003_phase_d.sql").read_text()


@pytest.fixture()
def store(tmp_path: Path) -> Path:
    s = tmp_path / "research"
    ingest.bootstrap_store(s)
    return s


@pytest.fixture()
def db(store: Path):
    conn = ingest.init_db(store / "manifest.db")
    conn.executescript(MIGRATION_003)
    yield conn
    conn.close()


@pytest.fixture()
def provider():
    return MockProvider()


class TestResearchAgent:
    def test_research_agent_tool_sequence(self, db, provider, store):
        calls = []

        def tracking_dispatch(task, db_conn, prov, auto_teach=True):
            from core.agents.research import run_research_agent

            def tracking_call_tool(name, inp):
                calls.append(name)
                if name == "retrieve":
                    return {"results": []}
                elif name == "generate":
                    return {"text": "mock content", "tokens_used": 10, "cost_usd": 0.0}
                elif name == "ingest":
                    return {"artifact_id": 1, "slug": "test-topic", "success": True}
                return {}

            task_obj = ResearchTask(task_type="research", topic="Test Topic", mode="concept")
            return run_research_agent(task_obj, tracking_call_tool)

        result = tracking_dispatch(None, None, None)
        assert calls == ["retrieve", "generate", "generate", "ingest"]
        assert "artifact_slug" in result

    def test_research_agent_empty_kb(self, db, provider, store):
        from core.agents.research import run_research_agent

        def mock_call_tool(name, inp):
            if name == "retrieve":
                return {"results": []}
            elif name == "generate":
                return {"text": "content", "tokens_used": 5, "cost_usd": 0.0}
            elif name == "ingest":
                return {"artifact_id": 1, "slug": "test", "success": True}
            return {}

        task = ResearchTask(task_type="research", topic="New Topic", mode="concept")
        result = run_research_agent(task, mock_call_tool)
        assert result["artifact_slug"] == "test"


class TestTeachingAgent:
    def test_teaching_agent_tool_sequence(self):
        from core.agents.teaching import run_teaching_agent

        calls = []

        def mock_call_tool(name, inp):
            calls.append(name)
            if name == "retrieve":
                return {"results": []}
            elif name == "generate":
                return {"text": "teaching content", "tokens_used": 10, "cost_usd": 0.0}
            elif name == "ingest":
                return {"artifact_id": 2, "slug": "test-mastery-checklist", "success": True}
            return {}

        task = TeachTask(task_type="teach", topic="Test Topic")
        result = run_teaching_agent(task, mock_call_tool)

        assert calls[0] == "retrieve"
        assert calls.count("generate") >= 4
        assert calls[-1] == "ingest"
        assert "checklist_slug" in result


class TestDispatcher:
    def test_dispatcher_research_only(self, db, provider, store):
        with patch.dict("os.environ", {"EVO_RESEARCH_STORE": str(store)}):
            task = ResearchTask(task_type="research", topic="Dispatch Test", mode="concept")
            result = dispatch(task, db, provider, auto_teach=False)

        assert isinstance(result, AgentRun)
        assert result.status == "complete"
        assert result.output is not None
        assert "artifact_slug" in result.output

    def test_dispatcher_auto_chain(self, db, provider, store):
        with patch.dict("os.environ", {"EVO_RESEARCH_STORE": str(store)}):
            task = ResearchTask(task_type="research", topic="Chain Test", mode="concept")
            result = dispatch(task, db, provider, auto_teach=True)

        assert isinstance(result, tuple)
        research_run, teach_run = result
        assert research_run.status == "complete"
        assert teach_run.status == "complete"
        assert "artifact_slug" in research_run.output
        assert "checklist_slug" in teach_run.output

    def test_dispatcher_teach_failure_isolated(self, db, provider, store):
        call_count = [0]
        original_chat = provider.chat

        def failing_chat(messages, context_chunks):
            call_count[0] += 1
            if call_count[0] > 4:
                raise RuntimeError("Teaching provider failure")
            return original_chat(messages, context_chunks)

        provider.chat = failing_chat

        with patch.dict("os.environ", {"EVO_RESEARCH_STORE": str(store)}):
            task = ResearchTask(task_type="research", topic="Isolated Test", mode="concept")
            result = dispatch(task, db, provider, auto_teach=True)

        assert isinstance(result, tuple)
        research_run, teach_run = result
        assert research_run.status == "complete"
        assert teach_run.status == "failed"

    def test_dispatcher_validates_task(self, db, provider, store):
        with patch.dict("os.environ", {"EVO_RESEARCH_STORE": str(store)}):
            task = ResearchTask(task_type="research", topic="", mode="concept")
            with pytest.raises(ValueError, match="non-empty"):
                dispatch(task, db, provider)
