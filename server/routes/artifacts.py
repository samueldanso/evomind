"""Artifact CRUD routes — list, detail, search, delete."""

from __future__ import annotations

import re
import sqlite3

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a plain dict for JSON serialization."""
    return {
        "id": row["id"],
        "slug": row["slug"],
        "title": row["title"],
        "summary": row["summary"],
        "tags": row["tags"],
        "topics": row["topics"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _fts_escape(query: str) -> str:
    """Wrap each token in double quotes so FTS5 treats special chars as literals."""
    return " ".join(
        f'"{t}"'
        for t in (tok.replace('"', "") for tok in query.strip().split())
        if t != ""
    )


@router.get("/api/artifacts")
async def list_artifacts(request: Request):
    if getattr(request.app.state, "startup_error", None):
        return JSONResponse(
            status_code=503,
            content={"error": request.app.state.startup_error},
        )

    db: sqlite3.Connection = request.app.state.db
    rows = db.execute("SELECT * FROM artifacts ORDER BY created_at DESC").fetchall()
    return [_row_to_dict(r) for r in rows]


@router.get("/api/artifacts/{slug}")
async def get_artifact(request: Request, slug: str):
    if getattr(request.app.state, "startup_error", None):
        return JSONResponse(
            status_code=503,
            content={"error": request.app.state.startup_error},
        )

    db: sqlite3.Connection = request.app.state.db
    row = db.execute("SELECT * FROM artifacts WHERE slug = ?", (slug,)).fetchone()
    if not row:
        return JSONResponse(status_code=404, content={"error": "Not found"})
    return _row_to_dict(row)


@router.get("/api/search")
async def search_artifacts(request: Request, q: str = ""):
    if getattr(request.app.state, "startup_error", None):
        return JSONResponse(
            status_code=503,
            content={"error": request.app.state.startup_error},
        )

    db: sqlite3.Connection = request.app.state.db
    query = q.strip()

    if not query:
        rows = db.execute("SELECT * FROM artifacts ORDER BY created_at DESC").fetchall()
        return [_row_to_dict(r) for r in rows]

    escaped = _fts_escape(query)
    if not escaped:
        return []

    try:
        rows = db.execute(
            """SELECT a.*
               FROM artifacts a
               JOIN artifacts_fts f ON a.id = f.rowid
               WHERE artifacts_fts MATCH ?
               ORDER BY rank""",
            (escaped,),
        ).fetchall()
    except Exception:
        # Fallback to LIKE search if FTS fails (e.g. table missing)
        pattern = f"%{query}%"
        rows = db.execute(
            "SELECT * FROM artifacts WHERE title LIKE ? OR summary LIKE ? ORDER BY created_at DESC",
            (pattern, pattern),
        ).fetchall()

    return [_row_to_dict(r) for r in rows]


@router.delete("/api/artifacts/{slug}")
async def delete_artifact(request: Request, slug: str):
    if getattr(request.app.state, "startup_error", None):
        return JSONResponse(
            status_code=503,
            content={"error": request.app.state.startup_error},
        )

    db: sqlite3.Connection = request.app.state.db
    row = db.execute("SELECT id FROM artifacts WHERE slug = ?", (slug,)).fetchone()
    if not row:
        return JSONResponse(status_code=404, content={"error": "Not found"})

    artifact_id = row["id"]

    # Delete embeddings for all chunks of this artifact
    db.execute(
        "DELETE FROM embeddings WHERE chunk_id IN (SELECT rowid FROM chunks WHERE artifact_id = ?)",
        (artifact_id,),
    )
    # Delete chunks
    db.execute("DELETE FROM chunks WHERE artifact_id = ?", (artifact_id,))
    # Delete artifact (FTS trigger handles artifacts_fts cleanup)
    db.execute("DELETE FROM artifacts WHERE id = ?", (artifact_id,))
    db.commit()

    return JSONResponse(status_code=204, content=None)
