"""Provider abstraction for LLM chat and embedding calls."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Protocol, cast


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
    def embed(self, texts: list[str], input_type: str = "search_document") -> list[list[float]]: ...
    def chat(self, messages: list[ChatMessage], context_chunks: list[str]) -> ChatResponse: ...


class BedrockProvider:
    def __init__(
        self,
        embed_model: str = "cohere.embed-v4:0",
        chat_model: str = "us.anthropic.claude-sonnet-4-6",
        region: str | None = None,
    ) -> None:
        resolved_region = region or os.environ.get("AWS_REGION", "us-east-1")
        try:
            import boto3
        except ImportError as exc:
            raise ValueError(
                "boto3 is required for BedrockProvider. Install it with: uv add boto3"
            ) from exc

        try:
            self.client = boto3.client("bedrock-runtime", region_name=resolved_region)
        except Exception as exc:
            raise ValueError(
                f"Failed to create Bedrock client in region {resolved_region!r}: {exc}"
            ) from exc

        self.embed_model = embed_model
        self.chat_model = chat_model
        self.region = resolved_region

    def embed(self, texts: list[str], input_type: str = "search_document") -> list[list[float]]:
        body = json.dumps(
            {
                "texts": texts,
                "input_type": input_type,
                "output_dimension": 1024,
                "embedding_types": ["float"],
            }
        )

        response = self.client.invoke_model(
            modelId=self.embed_model,
            body=body,
            contentType="application/json",
            accept="application/json",
        )

        response_body: dict[str, Any] = json.loads(response["body"].read())
        return cast(list[list[float]], response_body["embeddings"]["float"])

    def chat(self, messages: list[ChatMessage], context_chunks: list[str]) -> ChatResponse:
        context_block = "\n\n---\n\n".join(context_chunks)
        user_content = f"<context>\n\n{context_block}\n\n</context>\n\n{messages[-1].content}"

        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "system": "You are a research assistant. Answer using only the provided context chunks. Cite sources inline.",
                "messages": [{"role": "user", "content": user_content}],
            }
        )

        response = self.client.invoke_model(
            modelId=self.chat_model,
            body=body,
            contentType="application/json",
            accept="application/json",
        )

        response_body = json.loads(response["body"].read())
        content = response_body["content"][0]["text"]
        return ChatResponse(content=content, citations=[])


def get_provider(provider_name: str | None = None) -> Provider:
    name = provider_name or os.environ.get("EVO_LLM_PROVIDER", "openrouter")
    if name == "openrouter":
        from core.llm.openrouter import OpenRouterProvider

        return OpenRouterProvider()
    if name == "bedrock":
        return BedrockProvider()
    raise ValueError(f"Unknown provider: {name!r}. Expected 'openrouter' or 'bedrock'.")
