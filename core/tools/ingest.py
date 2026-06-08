"""Ingest tool — thin wrapper over v0.1.0 save_artifact + chunk_and_store."""

from __future__ import annotations

import struct
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from scripts.ingest import Artifact, chunk_and_store, save_artifact
from core.llm.bedrock import BedrockProvider
from core.tools.base import Tool

EMBED_BATCH_SIZE = 64


def _embed_new_chunks(db: sqlite3.Connection, artifact_id: int, provider: BedrockProvider) -> int:
    """Embed chunks belonging to the given artifact that have no embeddings yet."""
    try:
        rows = db.execute(
            """
            SELECT c.id, c.text
            FROM chunks c
            LEFT JOIN embeddings e ON c.id = e.chunk_id
            WHERE c.artifact_id = ? AND e.chunk_id IS NULL
            """,
            (artifact_id,),
        ).fetchall()
    except sqlite3.OperationalError:
        return 0

    if not rows:
        return 0

    chunks = [(row[0], row[1]) for row in rows]
    embedded = 0

    for batch_start in range(0, len(chunks), EMBED_BATCH_SIZE):
        batch = chunks[batch_start : batch_start + EMBED_BATCH_SIZE]
        texts = [text for _, text in batch]
        ids = [chunk_id for chunk_id, _ in batch]

        vectors = provider.embed(texts, input_type="search_document")

        for chunk_id, vector in zip(ids, vectors, strict=True):
            db.execute(
                "INSERT INTO embeddings (chunk_id, embedding) VALUES (?, ?)",
                (chunk_id, struct.pack(f"{len(vector)}f", *vector)),
            )

        db.commit()
        embedded += len(batch)

    return embedded


def build_ingest_tool(db: sqlite3.Connection, vault_path: Path) -> Tool:
    try:
        provider = BedrockProvider()
    except (ValueError, Exception):
        provider = None

    def execute(input: dict) -> dict:
        slug = input["slug"]
        title = input["title"]
        html_content = input["html_content"]
        summary = input["summary"]
        tags = ",".join(input.get("tags", []))

        html_dir = vault_path / "html"
        html_dir.mkdir(parents=True, exist_ok=True)
        html_path = html_dir / f"{slug}.html"
        html_path.write_text(html_content, encoding="utf-8")

        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        artifact = Artifact(
            slug=slug,
            title=title,
            summary=summary,
            tags=tags,
            topics="",
            html_path=str(html_path),
            md_path=None,
            created_at=now,
            updated_at=now,
        )

        save_artifact(db, vault_path, artifact)

        row = db.execute("SELECT id FROM artifacts WHERE slug = ?", (slug,)).fetchone()
        artifact_id = row[0] if row else 0

        chunk_and_store(db, artifact_id, html_path)

        chunks_embedded = 0
        if provider:
            chunks_embedded = _embed_new_chunks(db, artifact_id, provider)

        return {
            "artifact_id": artifact_id,
            "slug": slug,
            "chunks_embedded": chunks_embedded,
            "success": True,
        }

    return Tool(
        name="ingest",
        description="Write an artifact to the KB, chunk it, and embed for retrieval.",
        execute=execute,
    )
