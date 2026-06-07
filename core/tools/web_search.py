"""Web search tool — Phase D stub, always returns empty results."""

from __future__ import annotations

from core.tools.base import Tool


def build_web_search_tool() -> Tool:
    def execute(input: dict) -> dict:
        # Phase G: replace with real web_search (Brave/Tavily/Exa).
        return {"results": []}

    return Tool(
        name="web_search",
        description="Search the web. Phase D stub — always returns empty.",
        execute=execute,
    )
