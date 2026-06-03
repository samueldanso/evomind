"""Tests for lib/provider.py — Provider abstraction, factory, and MockProvider."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.provider import (
    BedrockProvider,
    ChatMessage,
    ChatResponse,
    get_provider,
)

EMBEDDING_DIM = 1024


class MockProvider:
    """Deterministic mock provider for testing — no real API calls."""

    def __init__(self) -> None:
        self.embed_calls: list[list[str]] = []

    def embed(self, texts: list[str], input_type: str = "search_document") -> list[list[float]]:
        self.embed_calls.append(texts)
        return [[0.0] * EMBEDDING_DIM for _ in texts]

    def chat(self, messages: list[ChatMessage], context_chunks: list[str]) -> ChatResponse:
        return ChatResponse(content="Mock response based on context.")


# --- BedrockProvider ---


def test_bedrock_provider_default_region(monkeypatch):
    monkeypatch.delenv("AWS_REGION", raising=False)
    with patch("boto3.client") as mock_client:
        provider = BedrockProvider()
    assert provider.region == "us-east-1"
    mock_client.assert_called_once_with("bedrock-runtime", region_name="us-east-1")


def test_bedrock_provider_custom_region(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "eu-west-1")
    with patch("boto3.client") as mock_client:
        provider = BedrockProvider()
    assert provider.region == "eu-west-1"
    mock_client.assert_called_once_with("bedrock-runtime", region_name="eu-west-1")


# --- Factory ---


def test_get_provider_default_is_bedrock(monkeypatch):
    monkeypatch.delenv("EVO_LLM_PROVIDER", raising=False)
    with patch("boto3.client"):
        provider = get_provider()
    assert isinstance(provider, BedrockProvider)


def test_get_provider_raises_unknown(monkeypatch):
    monkeypatch.setenv("EVO_LLM_PROVIDER", "unknown")
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider()


# --- MockProvider ---


def test_mock_provider_embed_returns_correct_dims():
    mock = MockProvider()
    result = mock.embed(["hello", "world"])
    assert len(result) == 2
    assert len(result[0]) == EMBEDDING_DIM
    assert all(v == 0.0 for v in result[0])


def test_mock_provider_embed_accepts_input_type():
    mock = MockProvider()
    result = mock.embed(["test"], input_type="search_query")
    assert len(result) == 1
    assert len(result[0]) == EMBEDDING_DIM


def test_mock_provider_chat_returns_response():
    mock = MockProvider()
    msgs = [ChatMessage(role="user", content="test")]
    resp = mock.chat(msgs, ["context chunk"])
    assert isinstance(resp, ChatResponse)
    assert resp.content != ""


# --- Live provider tests (gated) ---


@pytest.mark.skipif(not os.getenv("RUN_LIVE_LLM"), reason="set RUN_LIVE_LLM=1")
def test_bedrock_embed_live():
    provider = BedrockProvider()
    result = provider.embed(["Hello world"], input_type="search_document")
    assert len(result) == 1
    assert len(result[0]) == EMBEDDING_DIM


@pytest.mark.skipif(not os.getenv("RUN_LIVE_LLM"), reason="set RUN_LIVE_LLM=1")
def test_bedrock_chat_live():
    provider = BedrockProvider()
    msgs = [ChatMessage(role="user", content="What is 2+2?")]
    resp = provider.chat(msgs, ["Mathematics: 2+2=4"])
    assert resp.content != ""
