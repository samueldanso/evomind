"""Tests for lib/provider.py — Provider abstraction, factory, and MockProvider."""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.provider import (
    AnthropicProvider,
    ChatMessage,
    ChatResponse,
    OpenAIProvider,
    get_provider,
)

EMBEDDING_DIM = 1536


class MockProvider:
    """Deterministic mock provider for testing — no real API calls."""

    def __init__(self) -> None:
        self.embed_calls: list[list[str]] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.embed_calls.append(texts)
        return [[0.0] * EMBEDDING_DIM for _ in texts]

    def chat(self, messages: list[ChatMessage], context_chunks: list[str]) -> ChatResponse:
        return ChatResponse(content="Mock response based on context.")


# --- Key validation ---


def test_anthropic_provider_raises_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        AnthropicProvider()


def test_openai_provider_raises_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        OpenAIProvider()


# --- Factory ---


def test_get_provider_returns_anthropic(monkeypatch):
    monkeypatch.setenv("EVO_LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-fake")
    provider = get_provider()
    assert isinstance(provider, AnthropicProvider)


def test_get_provider_returns_openai(monkeypatch):
    monkeypatch.setenv("EVO_LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake")
    provider = get_provider()
    assert isinstance(provider, OpenAIProvider)


def test_get_provider_raises_unknown(monkeypatch):
    monkeypatch.setenv("EVO_LLM_PROVIDER", "unknown")
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider()


# --- Base URL override ---


def test_openai_base_url_override(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake")
    monkeypatch.setenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
    provider = OpenAIProvider()
    assert str(provider.client.base_url).rstrip("/") == "http://localhost:11434/v1"


def test_anthropic_base_url_override(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-fake")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "http://localhost:8080")
    provider = AnthropicProvider()
    assert "localhost:8080" in str(provider.client.base_url)


# --- MockProvider ---


def test_mock_provider_embed_returns_correct_dims():
    mock = MockProvider()
    result = mock.embed(["hello", "world"])
    assert len(result) == 2
    assert len(result[0]) == EMBEDDING_DIM
    assert all(v == 0.0 for v in result[0])


def test_mock_provider_chat_returns_response():
    mock = MockProvider()
    msgs = [ChatMessage(role="user", content="test")]
    resp = mock.chat(msgs, ["context chunk"])
    assert isinstance(resp, ChatResponse)
    assert resp.content != ""


# --- Live provider tests (gated) ---


@pytest.mark.skipif(not os.getenv("RUN_LIVE_LLM"), reason="set RUN_LIVE_LLM=1")
def test_openai_embed_live():
    provider = OpenAIProvider()
    result = provider.embed(["Hello world"])
    assert len(result) == 1
    assert len(result[0]) == EMBEDDING_DIM


@pytest.mark.skipif(not os.getenv("RUN_LIVE_LLM"), reason="set RUN_LIVE_LLM=1")
def test_anthropic_chat_live():
    provider = AnthropicProvider()
    msgs = [ChatMessage(role="user", content="What is 2+2?")]
    resp = provider.chat(msgs, ["Mathematics: 2+2=4"])
    assert resp.content != ""
