"""Ingest tool — thin wrapper over v0.1.0 save_artifact + chunk_and_store."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from scripts.ingest import Artifact, chunk_and_store, save_artifact
from core.tools.base import Tool


def build_ingest_tool(db: sqlite3.Connection, vault_path: Path) -> Tool:
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

        return {"artifact_id": artifact_id, "slug": slug, "success": True}

    return Tool(
        name="ingest",
        description="Write an artifact to the KB and chunk it.",
        execute=execute,
    )
