"""Retrieve tool — thin wrapper over v0.2.0 hybrid search."""

from __future__ import annotations

import sqlite3

from core.memory.retrieval import hybrid_search
from core.tools.base import Tool


def build_retrieve_tool(db: sqlite3.Connection, provider) -> Tool:
    def execute(input: dict) -> dict:
        query = input["query"]
        k = input.get("k", 5)
        embedding = provider.embed([query], input_type="search_query")[0]
        results = hybrid_search(db, query, embedding, limit=k)
        return {
            "results": [
                {
                    "chunk_id": r.chunk_id,
                    "artifact_id": None,
                    "slug": r.artifact_slug,
                    "title": r.artifact_title,
                    "snippet": r.text[:300],
                    "score": r.score,
                    "match_type": r.match_type,
                }
                for r in results
            ]
        }

    return Tool(
        name="retrieve",
        description="Hybrid semantic + keyword search over the KB.",
        execute=execute,
    )
