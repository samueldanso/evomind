"""Chat and health routes — moved verbatim from server.py."""

from __future__ import annotations

import contextlib
import sqlite3

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.llm.bedrock import BedrockProvider, ChatMessage
from core.memory.retrieval import hybrid_search

router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    limit: int = 5


@router.get("/health")
async def health(request: Request):
    if getattr(request.app.state, "startup_error", None):
        return JSONResponse(
            status_code=503,
            content={"status": "error", "error": request.app.state.startup_error},
        )

    db: sqlite3.Connection = request.app.state.db
    chunk_count = db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    embedding_count = 0
    with contextlib.suppress(Exception):
        embedding_count = db.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]

    return {
        "status": "ok",
        "db_path": request.app.state.db_path,
        "chunk_count": chunk_count,
        "embedding_count": embedding_count,
    }


@router.post("/chat")
async def chat(request: Request, body: ChatRequest):
    if getattr(request.app.state, "startup_error", None):
        return JSONResponse(
            status_code=503,
            content={"error": request.app.state.startup_error},
        )

    db: sqlite3.Connection = request.app.state.db
    provider: BedrockProvider = request.app.state.provider

    try:
        query_embedding = provider.embed([body.query], input_type="search_query")[0]
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": f"Embedding failed: {exc}"},
        )

    results = hybrid_search(db, body.query, query_embedding, limit=body.limit)

    try:
        response = provider.chat(
            [ChatMessage(role="user", content=body.query)],
            context_chunks=[r.text for r in results],
        )
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": f"Chat generation failed: {exc}"},
        )

    sources = [
        {
            "slug": r.artifact_slug,
            "title": r.artifact_title,
            "excerpt": r.text[:200],
            "score": r.score,
            "match_type": r.match_type,
        }
        for r in results
    ]

    return {"answer": response.content, "sources": sources}
