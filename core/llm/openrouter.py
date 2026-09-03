"""OpenRouter provider — free LLaMA chat + local fastembed embeddings."""

from __future__ import annotations

import os
from typing import Any

import httpx

from core.llm.bedrock import ChatMessage, ChatResponse, Citation

# Lazy-loaded fastembed model (downloaded on first use, cached after)
_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        from fastembed import TextEmbedding

        _embedder = TextEmbedding("BAAI/bge-small-en-v1.5")
    return _embedder


class OpenRouterProvider:
    """Provider using OpenRouter (free LLaMA 3.3 70B) for chat and fastembed for embeddings."""

    def __init__(
        self,
        chat_model: str = "meta-llama/llama-3.3-70b-instruct:free",
        api_key: str | None = None,
    ) -> None:
        self.chat_model = chat_model
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is required. Get a free key at https://openrouter.ai/keys"
            )
        self.base_url = "https://openrouter.ai/api/v1"

    def embed(self, texts: list[str], input_type: str = "search_document") -> list[list[float]]:
        """Embed texts locally using fastembed (ONNX, CPU). No API call."""
        embedder = _get_embedder()
        embeddings = list(embedder.embed(texts))
        return [e.tolist() for e in embeddings]

    def chat(self, messages: list[ChatMessage], context_chunks: list[str]) -> ChatResponse:
        """Generate a response via OpenRouter API."""
        context_block = "\n\n---\n\n".join(context_chunks)
        user_content = f"<context>\n\n{context_block}\n\n</context>\n\n{messages[-1].content}"

        payload: dict[str, Any] = {
            "model": self.chat_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a research assistant. Answer using only the provided context chunks. Cite sources inline.",
                },
                {"role": "user", "content": user_content},
            ],
            "max_tokens": 1024,
        }

        response = httpx.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return ChatResponse(content=content, citations=[])
