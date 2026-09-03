"""Ingest route — accept raw text, chunk, embed, and store."""

from __future__ import annotations

import re
import sqlite3
import struct

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.memory.chunker import chunk_text

router = APIRouter()

EMBEDDING_DIM = 384


class IngestRequest(BaseModel):
    title: str
    text: str
    tags: str = ""
    topics: str = ""


def _slugify(title: str) -> str:
    """Generate a URL-friendly slug from a title."""
    slug = title.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


@router.post("/api/ingest")
async def ingest(request: Request, body: IngestRequest):
    if getattr(request.app.state, "startup_error", None):
        return JSONResponse(
            status_code=503,
            content={"error": request.app.state.startup_error},
        )

    db: sqlite3.Connection = request.app.state.db
    provider = request.app.state.provider

    if not body.title.strip():
        return JSONResponse(status_code=400, content={"error": "Title is required"})
    if not body.text.strip():
        return JSONResponse(status_code=400, content={"error": "Text content is required"})

    slug = _slugify(body.title)

    # Check for slug collision and make unique
    existing = db.execute("SELECT 1 FROM artifacts WHERE slug = ?", (slug,)).fetchone()
    if existing:
        count = db.execute(
            "SELECT COUNT(*) FROM artifacts WHERE slug LIKE ?", (f"{slug}%",)
        ).fetchone()[0]
        slug = f"{slug}-{count}"

    # 1. Insert artifact
    try:
        cursor = db.execute(
            "INSERT INTO artifacts (slug, title, summary, tags, topics) VALUES (?, ?, ?, ?, ?)",
            (slug, body.title.strip(), body.text[:500], body.tags, body.topics),
        )
        artifact_id = cursor.lastrowid
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to create artifact: {exc}"},
        )

    # 2. Chunk the text
    chunks = chunk_text(body.text)
    if not chunks:
        db.commit()
        return {"slug": slug, "title": body.title.strip(), "chunks": 0}

    # 3. Insert chunks
    chunk_ids_texts: list[tuple[int, str]] = []
    for chunk in chunks:
        cur = db.execute(
            "INSERT INTO chunks (artifact_id, text, char_start, char_end) VALUES (?, ?, ?, ?)",
            (artifact_id, chunk.text, chunk.char_start, chunk.char_end),
        )
        chunk_ids_texts.append((cur.lastrowid, chunk.text))

    # 4. Embed chunks
    try:
        texts = [t for _, t in chunk_ids_texts]
        embeddings = provider.embed(texts, input_type="search_document")
    except Exception as exc:
        # Commit what we have (artifact + chunks) even if embedding fails
        db.commit()
        return JSONResponse(
            status_code=500,
            content={"error": f"Embedding failed: {exc}", "slug": slug},
        )

    # 5. Store embeddings
    for (chunk_id, _), embedding in zip(chunk_ids_texts, embeddings):
        blob = struct.pack(f"{len(embedding)}f", *embedding)
        db.execute(
            "INSERT INTO embeddings (chunk_id, embedding) VALUES (?, ?)",
            (chunk_id, blob),
        )

    db.commit()

    return {"slug": slug, "title": body.title.strip(), "chunks": len(chunk_ids_texts)}
