#!/usr/bin/env python3
"""EvoResearch ingest CLI — save, search, and list research artifacts."""

import argparse
import json
import os
import shutil
import sqlite3
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.chunker import chunk_text, extract_text

_DEFAULT_STORE = (
    Path.home()
    / "Library"
    / "Mobile Documents"
    / "iCloud~md~obsidian"
    / "Documents"
    / "Samuel's Vault"
    / "HomeOS"
    / "Knowledge"
    / "Research"
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS artifacts (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  slug        TEXT UNIQUE NOT NULL,
  title       TEXT NOT NULL,
  summary     TEXT NOT NULL,
  tags        TEXT NOT NULL,
  topics      TEXT NOT NULL,
  html_path   TEXT NOT NULL,
  md_path     TEXT,
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS artifacts_fts USING fts5(
  slug,
  title,
  summary,
  tags,
  topics,
  content='artifacts',
  content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS artifacts_ai AFTER INSERT ON artifacts BEGIN
  INSERT INTO artifacts_fts(rowid, slug, title, summary, tags, topics)
  VALUES (new.id, new.slug, new.title, new.summary, new.tags, new.topics);
END;

CREATE TRIGGER IF NOT EXISTS artifacts_au AFTER UPDATE ON artifacts BEGIN
  INSERT INTO artifacts_fts(artifacts_fts, rowid, slug, title, summary, tags, topics)
  VALUES ('delete', old.id, old.slug, old.title, old.summary, old.tags, old.topics);
  INSERT INTO artifacts_fts(rowid, slug, title, summary, tags, topics)
  VALUES (new.id, new.slug, new.title, new.summary, new.tags, new.topics);
END;

CREATE TRIGGER IF NOT EXISTS artifacts_ad AFTER DELETE ON artifacts BEGIN
  DELETE FROM artifacts_fts WHERE rowid=old.id;
END;

CREATE TABLE IF NOT EXISTS chunks (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  artifact_id INTEGER NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
  ordinal     INTEGER NOT NULL,
  text        TEXT NOT NULL,
  char_start  INTEGER NOT NULL,
  char_end    INTEGER NOT NULL,
  created_at  TEXT NOT NULL,
  UNIQUE(artifact_id, ordinal)
);

CREATE INDEX IF NOT EXISTS idx_chunks_artifact ON chunks(artifact_id);
"""


@dataclass
class Artifact:
    slug: str
    title: str
    summary: str
    tags: str
    topics: str
    html_path: str
    md_path: str | None
    created_at: str
    updated_at: str


def get_store_path() -> Path:
    env = os.environ.get("EVO_RESEARCH_STORE")
    return Path(env) if env else _DEFAULT_STORE


def bootstrap_store(store: Path) -> Path:
    (store / "html").mkdir(parents=True, exist_ok=True)
    (store / "summaries").mkdir(parents=True, exist_ok=True)
    return store


def init_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _date_str() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def write_companion_md(store: Path, artifact: Artifact) -> Path:
    md_path = store / "summaries" / f"{artifact.slug}.md"
    tags_list = [t.strip() for t in artifact.tags.split(",") if t.strip()]
    topics_list = [t.strip() for t in artifact.topics.split(",") if t.strip()]
    tags_yaml = "\n".join(f"  - {t}" for t in tags_list)
    topics_yaml = "\n".join(f"  - {t}" for t in topics_list)
    content = f"""---
title: "{artifact.title}"
slug: {artifact.slug}
tags:
{tags_yaml}
topics:
{topics_yaml}
summary: >
  {artifact.summary}
created_at: {artifact.created_at}
html_path: {artifact.html_path}
---

# {artifact.title}

{artifact.summary}
"""
    md_path.write_text(content, encoding="utf-8")
    return md_path


def save_artifact(db: sqlite3.Connection, store: Path, artifact: Artifact) -> None:
    db.execute(
        """
        INSERT INTO artifacts
          (slug, title, summary, tags, topics, html_path, md_path, created_at, updated_at)
        VALUES
          (:slug, :title, :summary, :tags, :topics, :html_path, :md_path, :created_at, :updated_at)
        ON CONFLICT(slug) DO UPDATE SET
          title=excluded.title,
          summary=excluded.summary,
          tags=excluded.tags,
          topics=excluded.topics,
          html_path=excluded.html_path,
          md_path=excluded.md_path,
          updated_at=excluded.updated_at
        """,
        asdict(artifact),
    )
    db.commit()


def chunk_and_store(conn: sqlite3.Connection, artifact_id: int, html_path: Path) -> int:
    """Extract text from HTML, chunk it, and store chunks in the DB."""
    html = html_path.read_text(encoding="utf-8")
    text = extract_text(html)
    chunks = chunk_text(text)

    if not chunks:
        print(f"warning: no chunks produced for artifact {artifact_id}", file=sys.stderr)
        return 0

    conn.execute("DELETE FROM chunks WHERE artifact_id = ?", (artifact_id,))
    now = _now_iso()
    conn.executemany(
        "INSERT INTO chunks (artifact_id, ordinal, text, char_start, char_end, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [(artifact_id, c.ordinal, c.text, c.char_start, c.char_end, now) for c in chunks],
    )
    conn.commit()
    return len(chunks)


def _fts_escape(query: str) -> str:
    # Wrap each token in double quotes so FTS5 treats hyphens, wildcards, and
    # other special chars as literals. Strip embedded " first — FTS5 phrase
    # literals have no escape sequence for " and would produce a syntax error.
    tokens = [t.replace('"', "") for t in query.split()]
    return " ".join(f'"{t}"' for t in tokens if t)


def search_artifacts(db: sqlite3.Connection, query: str) -> list[dict]:
    rows = db.execute(
        """
        SELECT a.*
        FROM artifacts a
        JOIN artifacts_fts f ON a.id = f.rowid
        WHERE artifacts_fts MATCH ?
        ORDER BY bm25(artifacts_fts)
        """,
        (_fts_escape(query),),
    ).fetchall()
    return [dict(row) for row in rows]


def list_artifacts(db: sqlite3.Connection) -> list[dict]:
    rows = db.execute("SELECT * FROM artifacts ORDER BY created_at DESC").fetchall()
    return [dict(row) for row in rows]


def cmd_ingest(args: argparse.Namespace) -> None:
    src_html = Path(args.html)
    if not src_html.exists():
        print(f"error: HTML file not found: {src_html}", file=sys.stderr)
        sys.exit(1)

    store = get_store_path()
    bootstrap_store(store)
    db = init_db(store / "manifest.db")

    now = _now_iso()
    dest_html = store / "html" / f"{args.slug}-{_date_str()}.html"
    shutil.copy2(str(src_html), str(dest_html))

    artifact = Artifact(
        slug=args.slug,
        title=args.title,
        summary=args.summary,
        tags=args.tags,
        topics=args.topics,
        html_path=str(dest_html),
        md_path=None,
        created_at=now,
        updated_at=now,
    )

    md_path = write_companion_md(store, artifact)
    artifact.md_path = str(md_path)

    save_artifact(db, store, artifact)

    row = db.execute("SELECT id FROM artifacts WHERE slug = ?", (args.slug,)).fetchone()
    artifact_id = row["id"]
    n_chunks = chunk_and_store(db, artifact_id, dest_html)

    db.close()

    print(f"saved: {args.slug}")
    print(f"  html → {dest_html}")
    print(f"  md   → {md_path}")
    print(f"  chunks → {n_chunks}")


def cmd_search(args: argparse.Namespace) -> None:
    store = get_store_path()
    db = init_db(store / "manifest.db")
    results = search_artifacts(db, args.search)
    db.close()
    print(json.dumps(results, indent=2))


def cmd_list(_args: argparse.Namespace) -> None:
    store = get_store_path()
    db = init_db(store / "manifest.db")
    results = list_artifacts(db)
    db.close()
    print(json.dumps(results, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EvoResearch artifact ingest and query CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--html", metavar="PATH", help="Source HTML file to ingest")
    group.add_argument("--search", metavar="QUERY", help="Full-text search query")
    group.add_argument("--list", action="store_true", help="List all artifacts as JSON")

    parser.add_argument("--title", help="Artifact title (required with --html)")
    parser.add_argument("--slug", help="URL-safe slug (required with --html)")
    parser.add_argument("--tags", help="Comma-separated tags (required with --html)")
    parser.add_argument("--topics", help="Comma-separated topics (required with --html)")
    parser.add_argument("--summary", help="Short summary (required with --html)")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.html:
        required = ["title", "slug", "tags", "topics", "summary"]
        missing = [f"--{r}" for r in required if not getattr(args, r)]
        if missing:
            parser.error(f"--html requires: {', '.join(missing)}")
        cmd_ingest(args)
    elif args.search is not None:
        if not args.search.strip():
            parser.error("--search requires a non-empty query")
        cmd_search(args)
    else:
        cmd_list(args)


if __name__ == "__main__":
    main()
