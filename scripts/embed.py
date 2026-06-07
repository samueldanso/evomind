#!/usr/bin/env python3
"""EvoResearch embed pipeline — compute and store chunk embeddings.

Usage:
    uv run scripts/embed.py [--incremental | --rebuild] [--db PATH]
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm.bedrock import BedrockProvider
from core.memory.db import default_db_path, load_sqlite_vec, open_db

BATCH_SIZE = 64
MAX_RETRIES = 3


def get_unembedded_chunks(conn: sqlite3.Connection) -> list[tuple[int, str]]:
    """Return (chunk_id, text) for chunks without embeddings."""
    rows = conn.execute("""
        SELECT c.id, c.text
        FROM chunks c
        LEFT JOIN embeddings e ON c.id = e.chunk_id
        WHERE e.chunk_id IS NULL
    """).fetchall()
    return [(row[0], row[1]) for row in rows]


def get_all_chunks(conn: sqlite3.Connection) -> list[tuple[int, str]]:
    """Return all (chunk_id, text) pairs."""
    rows = conn.execute("SELECT id, text FROM chunks").fetchall()
    return [(row[0], row[1]) for row in rows]


def embed_chunks(
    conn: sqlite3.Connection,
    chunks: list[tuple[int, str]],
    provider: BedrockProvider,
) -> int:
    """Embed chunks in batches, write to embeddings table. Returns count embedded."""
    total = len(chunks)
    if total == 0:
        return 0

    embedded = 0
    for batch_start in range(0, total, BATCH_SIZE):
        batch = chunks[batch_start : batch_start + BATCH_SIZE]
        texts = [text for _, text in batch]
        ids = [chunk_id for chunk_id, _ in batch]

        vectors = _embed_with_retry(provider, texts)

        for chunk_id, vector in zip(ids, vectors, strict=True):
            conn.execute(
                "INSERT INTO embeddings (chunk_id, embedding) VALUES (?, ?)",
                (chunk_id, _serialize_vector(vector)),
            )

        conn.commit()
        embedded += len(batch)
        pct = int(embedded / total * 100)
        print(f"Embedded {embedded}/{total} chunks ({pct}%)")

    return embedded


def _embed_with_retry(provider: BedrockProvider, texts: list[str]) -> list[list[float]]:
    """Call provider.embed with exponential backoff on transient errors."""
    for attempt in range(MAX_RETRIES):
        try:
            return provider.embed(texts, input_type="search_document")
        except Exception as exc:
            if attempt == MAX_RETRIES - 1:
                raise
            wait = 2**attempt
            print(f"Embed error ({exc}), retrying in {wait}s...", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError("Unreachable")


def _serialize_vector(vector: list[float]) -> bytes:
    """Serialize a float vector to bytes for sqlite-vec."""
    import struct

    return struct.pack(f"{len(vector)}f", *vector)


def run_incremental(conn: sqlite3.Connection, provider: BedrockProvider) -> int:
    chunks = get_unembedded_chunks(conn)
    if not chunks:
        print("All chunks already embedded. Nothing to do.")
        return 0
    print(f"Found {len(chunks)} unembedded chunks.")
    return embed_chunks(conn, chunks, provider)


def run_rebuild(conn: sqlite3.Connection, provider: BedrockProvider) -> int:
    chunks = get_all_chunks(conn)
    total = len(chunks)
    confirm = input(f"Re-embedding all {total} chunks. Confirm? [y/N] ")
    if confirm.strip().lower() != "y":
        print("Aborted.")
        sys.exit(0)

    conn.execute("DELETE FROM embeddings")
    conn.commit()
    print(f"Cleared embeddings. Re-embedding {total} chunks...")
    return embed_chunks(conn, chunks, provider)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="EvoResearch embedding pipeline")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--incremental",
        action="store_true",
        default=True,
        help="Embed only new chunks (default)",
    )
    group.add_argument(
        "--rebuild",
        action="store_true",
        default=False,
        help="Drop all embeddings and re-embed everything",
    )
    parser.add_argument("--db", type=Path, default=None, help="Path to manifest.db")
    args = parser.parse_args(argv)

    db_path = args.db or default_db_path()
    if not db_path.exists():
        print(f"ERROR: DB not found at {db_path}", file=sys.stderr)
        sys.exit(1)

    conn = open_db(db_path)
    load_sqlite_vec(conn)

    try:
        provider = BedrockProvider()
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if args.rebuild:
            count = run_rebuild(conn, provider)
        else:
            count = run_incremental(conn, provider)
        print(f"Done. {count} chunks embedded.")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
