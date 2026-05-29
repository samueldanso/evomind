"""FastAPI chat server — retrieval + LLM chat over the EvoResearch corpus."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

import os
import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from lib.db import default_db_path, load_sqlite_vec, open_db
from lib.provider import AnthropicProvider, ChatMessage, OpenAIProvider
from lib.retrieval import hybrid_search


class ChatRequest(BaseModel):
    query: str
    limit: int = 5


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_path = default_db_path()
    try:
        conn = open_db(db_path)
        load_sqlite_vec(conn)
    except Exception as exc:
        raise RuntimeError(f"Failed to open database: {exc}") from exc

    try:
        embed_provider = OpenAIProvider()
    except ValueError as exc:
        app.state.startup_error = f"Embedding provider init failed: {exc}"
        app.state.db = None
        app.state.embed_provider = None
        app.state.chat_provider = None
        yield
        return

    try:
        chat_provider = AnthropicProvider()
    except ValueError as exc:
        app.state.startup_error = f"Chat provider init failed: {exc}"
        app.state.db = None
        app.state.embed_provider = None
        app.state.chat_provider = None
        yield
        return

    app.state.db = conn
    app.state.embed_provider = embed_provider
    app.state.chat_provider = chat_provider
    app.state.startup_error = None
    app.state.db_path = str(db_path)
    yield
    conn.close()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health(request: Request):
    if getattr(request.app.state, "startup_error", None):
        return JSONResponse(
            status_code=503,
            content={"status": "error", "error": request.app.state.startup_error},
        )

    db: sqlite3.Connection = request.app.state.db
    chunk_count = db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    embedding_count = 0
    try:
        embedding_count = db.execute(
            "SELECT COUNT(*) FROM embeddings"
        ).fetchone()[0]
    except Exception:
        pass

    return {
        "status": "ok",
        "db_path": request.app.state.db_path,
        "chunk_count": chunk_count,
        "embedding_count": embedding_count,
    }


@app.post("/chat")
async def chat(request: Request, body: ChatRequest):
    if getattr(request.app.state, "startup_error", None):
        return JSONResponse(
            status_code=503,
            content={"error": request.app.state.startup_error},
        )

    db: sqlite3.Connection = request.app.state.db
    embed_provider: OpenAIProvider = request.app.state.embed_provider
    chat_provider: AnthropicProvider = request.app.state.chat_provider

    try:
        query_embedding = embed_provider.embed([body.query])[0]
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": f"Embedding failed: {exc}"},
        )

    results = hybrid_search(db, body.query, query_embedding, limit=body.limit)

    context = "\n\n---\n\n".join(r.text for r in results)

    try:
        response = chat_provider.chat(
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app, host="127.0.0.1", port=int(os.getenv("EVO_CHAT_PORT", "8765"))
    )
