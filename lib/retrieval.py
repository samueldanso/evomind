"""Hybrid retrieval layer — FTS5 + vector search via sqlite-vec."""

from __future__ import annotations

import sqlite3
import struct
from dataclasses import dataclass


@dataclass
class RetrievalResult:
    chunk_id: int
    artifact_slug: str
    artifact_title: str
    text: str
    score: float
    match_type: str


def fts_search(
    db: sqlite3.Connection, query: str, limit: int = 10
) -> list[RetrievalResult]:
    try:
        rows = db.execute(
            """
            SELECT chunks.id, artifacts.slug, artifacts.title, chunks.text,
                   bm25(chunks_fts) AS score
            FROM chunks_fts
            JOIN chunks ON chunks.rowid = chunks_fts.rowid
            JOIN artifacts ON chunks.artifact_id = artifacts.id
            WHERE chunks_fts MATCH ?
            ORDER BY score
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()
    except Exception:
        return []

    results = []
    for row in rows:
        results.append(
            RetrievalResult(
                chunk_id=row[0],
                artifact_slug=row[1],
                artifact_title=row[2],
                text=row[3],
                score=abs(row[4]),
                match_type="fts",
            )
        )
    return results


def vec_search(
    db: sqlite3.Connection, query_embedding: list[float], limit: int = 10
) -> list[RetrievalResult]:
    blob = struct.pack(f"{len(query_embedding)}f", *query_embedding)
    try:
        rows = db.execute(
            "SELECT chunk_id, distance FROM embeddings WHERE embedding MATCH ? AND k=? ORDER BY distance",
            (blob, limit),
        ).fetchall()
    except Exception:
        return []

    if not rows:
        return []

    results = []
    for row in rows:
        chunk_id = row[0]
        distance = row[1]
        detail = db.execute(
            """
            SELECT chunks.text, artifacts.slug, artifacts.title
            FROM chunks
            JOIN artifacts ON chunks.artifact_id = artifacts.id
            WHERE chunks.id = ?
            """,
            (chunk_id,),
        ).fetchone()
        if detail is None:
            continue
        results.append(
            RetrievalResult(
                chunk_id=chunk_id,
                artifact_slug=detail[0 + 1],
                artifact_title=detail[0 + 2],
                text=detail[0],
                score=1.0 / (1.0 + distance),
                match_type="vec",
            )
        )
    return results


def hybrid_search(
    db: sqlite3.Connection,
    query: str,
    query_embedding: list[float],
    limit: int = 5,
) -> list[RetrievalResult]:
    fts_results = fts_search(db, query, limit * 2)
    vec_results = vec_search(db, query_embedding, limit * 2)

    merged: dict[int, RetrievalResult] = {}

    for r in fts_results:
        merged[r.chunk_id] = r

    for r in vec_results:
        if r.chunk_id in merged:
            existing = merged[r.chunk_id]
            if r.score > existing.score:
                merged[r.chunk_id] = RetrievalResult(
                    chunk_id=r.chunk_id,
                    artifact_slug=r.artifact_slug,
                    artifact_title=r.artifact_title,
                    text=r.text,
                    score=r.score,
                    match_type="hybrid",
                )
            else:
                merged[r.chunk_id] = RetrievalResult(
                    chunk_id=existing.chunk_id,
                    artifact_slug=existing.artifact_slug,
                    artifact_title=existing.artifact_title,
                    text=existing.text,
                    score=existing.score,
                    match_type="hybrid",
                )
        else:
            merged[r.chunk_id] = r

    ranked = sorted(merged.values(), key=lambda r: r.score, reverse=True)
    return ranked[:limit]
