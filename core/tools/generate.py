"""Generate tool — thin wrapper over v0.2.0 Provider.chat()."""

from __future__ import annotations

from core.llm.bedrock import ChatMessage
from core.tools.base import Tool


def build_generate_tool(provider) -> Tool:
    def execute(input: dict) -> dict:
        messages = [ChatMessage(role=m["role"], content=m["content"]) for m in input["messages"]]
        context_chunks = [c.get("text", "") for c in (input.get("context") or [])]
        response = provider.chat(messages, context_chunks)
        tokens_used = len(response.content) // 4
        return {
            "text": response.content,
            "tokens_used": tokens_used,
            "cost_usd": 0.0,
        }

    return Tool(
        name="generate",
        description="Generate text via the LLM provider.",
        execute=execute,
    )
