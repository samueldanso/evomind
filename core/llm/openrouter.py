"""OpenRouter provider — free Gemma chat + local fastembed embeddings."""

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
    """Provider using OpenRouter (free models) for chat and fastembed for embeddings."""

    # Free models ordered by quality — falls through on failure
    FREE_MODELS = [
        "google/gemma-4-26b-a4b-it:free",
        "nvidia/nemotron-3-ultra-550b-a55b:free",
        "minimax/minimax-m3:free",
    ]

    def __init__(
        self,
        chat_model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.chat_model = chat_model or self.FREE_MODELS[0]
        self.fallback_models = [m for m in self.FREE_MODELS if m != self.chat_model]
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
        """Generate a response via OpenRouter API with model fallback."""
        context_block = "\n\n---\n\n".join(context_chunks)
        user_content = f"<context>\n\n{context_block}\n\n</context>\n\n{messages[-1].content}"

        models_to_try = [self.chat_model] + self.fallback_models
        last_error: Exception | None = None

        for model in models_to_try:
            payload: dict[str, Any] = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a research assistant. Answer using only the provided context chunks. Cite sources inline.",
                    },
                    {"role": "user", "content": user_content},
                ],
                "max_tokens": 1024,
            }

            try:
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
            except Exception as exc:
                last_error = exc
                continue

        raise last_error or RuntimeError("All models failed")
