"""Tests for core/tools/ — Tool protocol, registry, and all Phase D tools."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

import scripts.ingest as ingest
from core.llm.bedrock import ChatResponse
from core.tools.base import Tool, ToolRegistry
from core.tools.generate import build_generate_tool
from core.tools.ingest import build_ingest_tool
from core.tools.retrieve import build_retrieve_tool
from core.tools.web_search import build_web_search_tool


class MockProvider:
    def embed(self, texts: list[str], input_type: str = "search_document") -> list[list[float]]:
        return [[0.1] * 1024 for _ in texts]

    def chat(self, messages, context_chunks):
        return ChatResponse(content="mock response", citations=[])


@pytest.fixture()
def store(tmp_path: Path) -> Path:
    s = tmp_path / "research"
    ingest.bootstrap_store(s)
    return s


@pytest.fixture()
def db(store: Path):
    conn = ingest.init_db(store / "manifest.db")
    yield conn
    conn.close()


@pytest.fixture()
def provider():
    return MockProvider()


class TestRetrieveTool:
    def test_retrieve_tool_protocol(self, db, provider):
        tool = build_retrieve_tool(db, provider)
        assert isinstance(tool, Tool)
        assert tool.name == "retrieve"

    def test_retrieve_empty_corpus(self, db, provider):
        tool = build_retrieve_tool(db, provider)
        result = tool.execute({"query": "nonexistent topic"})
        assert result == {"results": []}

    def test_retrieve_output_shape(self, db, store, provider):
        html_path = store / "html" / "test.html"
        html_path.write_text("<html><body><p>KV Cache is a mechanism.</p></body></html>")
        artifact = ingest.Artifact(
            slug="kv-cache",
            title="KV Cache",
            summary="About KV Cache",
            tags="ai",
            topics="llm",
            html_path=str(html_path),
            md_path=None,
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
        ingest.save_artifact(db, store, artifact)
        row = db.execute("SELECT id FROM artifacts WHERE slug = 'kv-cache'").fetchone()
        ingest.chunk_and_store(db, row[0], html_path)

        tool = build_retrieve_tool(db, provider)
        result = tool.execute({"query": "KV Cache"})
        assert "results" in result
        if result["results"]:
            r = result["results"][0]
            assert "chunk_id" in r
            assert "slug" in r
            assert "title" in r
            assert "snippet" in r
            assert "score" in r
            assert "match_type" in r


class TestGenerateTool:
    def test_generate_tool_protocol(self, provider):
        tool = build_generate_tool(provider)
        assert isinstance(tool, Tool)
        assert tool.name == "generate"

    def test_generate_output_shape(self, provider):
        tool = build_generate_tool(provider)
        result = tool.execute({"messages": [{"role": "user", "content": "hello"}]})
        assert "text" in result
        assert "tokens_used" in result
        assert "cost_usd" in result

    def test_generate_cost_zero(self, provider):
        tool = build_generate_tool(provider)
        result = tool.execute({"messages": [{"role": "user", "content": "hello"}]})
        assert result["cost_usd"] == 0.0


class TestIngestTool:
    def test_ingest_tool_protocol(self, db, store):
        tool = build_ingest_tool(db, store)
        assert isinstance(tool, Tool)
        assert tool.name == "ingest"

    def test_ingest_writes_to_db(self, db, store):
        tool = build_ingest_tool(db, store)
        result = tool.execute({
            "title": "Test Article",
            "slug": "test-article",
            "html_content": "<html><body><p>Content here.</p></body></html>",
            "summary": "A test",
            "tags": ["ai", "test"],
        })
        assert result["success"] is True
        assert result["slug"] == "test-article"
        row = db.execute("SELECT id FROM artifacts WHERE slug = 'test-article'").fetchone()
        assert row is not None

    def test_ingest_idempotent(self, db, store):
        tool = build_ingest_tool(db, store)
        payload = {
            "title": "Test Article",
            "slug": "test-article",
            "html_content": "<html><body><p>Content.</p></body></html>",
            "summary": "A test",
            "tags": ["ai"],
        }
        tool.execute(payload)
        tool.execute(payload)
        count = db.execute("SELECT COUNT(*) FROM artifacts WHERE slug = 'test-article'").fetchone()[0]
        assert count == 1


class TestWebSearchTool:
    def test_web_search_stub(self):
        tool = build_web_search_tool()
        assert isinstance(tool, Tool)
        assert tool.name == "web_search"
        result = tool.execute({"query": "anything"})
        assert result == {"results": []}


class TestToolRegistry:
    def test_registry_register_get(self):
        registry = ToolRegistry()
        tool = Tool(name="test", description="A test tool", execute=lambda x: x)
        registry.register(tool)
        assert registry.get("test") is tool

    def test_registry_unknown_tool_raises(self):
        registry = ToolRegistry()
        with pytest.raises(KeyError, match="not registered"):
            registry.get("nonexistent")

    def test_registry_build_for_agent(self, db, provider, store):
        registry = ToolRegistry()
        registry.register(build_retrieve_tool(db, provider))
        registry.register(build_generate_tool(provider))
        registry.register(build_ingest_tool(db, store))
        registry.register(build_web_search_tool())

        agent_tools = registry.build_for_agent("research_agent")
        assert set(agent_tools.keys()) == {"retrieve", "generate", "ingest"}
        assert "web_search" not in agent_tools
