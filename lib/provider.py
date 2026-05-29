"""Provider abstraction for LLM chat and embedding calls."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class Citation:
    artifact_slug: str
    title: str
    excerpt: str
    char_start: int
    char_end: int


@dataclass
class ChatResponse:
    content: str
    citations: list[Citation] = field(default_factory=list)


class Provider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...
    def chat(self, messages: list[ChatMessage], context_chunks: list[str]) -> ChatResponse: ...


class AnthropicProvider:
    def __init__(self, model: str = "claude-3-5-haiku-20241022") -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is required for AnthropicProvider"
            )
        import anthropic

        base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        self.client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Anthropic does not support embeddings")

    def chat(self, messages: list[ChatMessage], context_chunks: list[str]) -> ChatResponse:
        context_block = "\n\n".join(
            f"[{i + 1}] {chunk}" for i, chunk in enumerate(context_chunks)
        )
        system_prompt = (
            "You are a research assistant. Answer using only the provided context chunks. "
            "Cite sources using [N] notation.\n\n"
            f"Context:\n{context_block}"
        )

        api_messages = [{"role": m.role, "content": m.content} for m in messages]

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=api_messages,
        )

        content = response.content[0].text if response.content else ""
        return ChatResponse(content=content)


class OpenAIProvider:
    def __init__(self, embed_model: str = "text-embedding-3-small") -> None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required for OpenAIProvider"
            )
        import openai

        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.embed_model = embed_model

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(model=self.embed_model, input=texts)
        return [item.embedding for item in response.data]

    def chat(self, messages: list[ChatMessage], context_chunks: list[str]) -> ChatResponse:
        raise NotImplementedError("Use AnthropicProvider for chat")


def get_provider(provider_name: str | None = None) -> Provider:
    name = provider_name or os.environ.get("EVO_LLM_PROVIDER", "anthropic")
    if name == "anthropic":
        return AnthropicProvider()
    if name == "openai":
        return OpenAIProvider()
    raise ValueError(f"Unknown provider: {name!r}. Expected 'anthropic' or 'openai'.")
