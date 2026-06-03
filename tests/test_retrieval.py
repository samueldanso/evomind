"""Tests for lib/retrieval.py — hybrid FTS5 + vector search."""

import sqlite3
import struct
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent))

import migrate

from lib.retrieval import fts_search, hybrid_search, vec_search

MIGRATIONS_DIR = Path(__file__).parent.parent / "scripts" / "migrations"
EMBEDDING_DIM = 1024


def _serialize_vector(vector: list[float]) -> bytes:
    return struct.pack(f"{len(vector)}f", *vector)


def _make_vector(first_val: float) -> list[float]:
    """Create a 1024-dim vector with first_val at index 0, rest zeros."""
    vec = [0.0] * EMBEDDING_DIM
    vec[0] = first_val
    return vec


@pytest.fixture()
def retrieval_db(tmp_path: Path) -> sqlite3.Connection:
    """Fresh DB with migration 002, chunks_fts, and sample data for retrieval tests."""
    db_path = tmp_path / "manifest.db"
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row

    conn.execute("""
        CREATE TABLE artifacts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            slug        TEXT NOT NULL UNIQUE,
            title       TEXT NOT NULL,
            summary     TEXT NOT NULL,
            tags        TEXT NOT NULL DEFAULT '',
            topics      TEXT NOT NULL DEFAULT '',
            html_path   TEXT,
            md_path     TEXT,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        )
    """)
    conn.commit()

    migrate.apply_migrations(conn, MIGRATIONS_DIR, skip_backup_check=True)

    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
            text,
            content='chunks',
            content_rowid='rowid'
        )
    """)
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS chunks_fts_ai AFTER INSERT ON chunks BEGIN
            INSERT INTO chunks_fts(rowid, text) VALUES (new.rowid, new.text);
        END
    """)
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS chunks_fts_ad AFTER DELETE ON chunks BEGIN
            INSERT INTO chunks_fts(chunks_fts, rowid, text) VALUES ('delete', old.rowid, old.text);
        END
    """)
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS chunks_fts_au AFTER UPDATE ON chunks BEGIN
            INSERT INTO chunks_fts(chunks_fts, rowid, text) VALUES ('delete', old.rowid, old.text);
            INSERT INTO chunks_fts(rowid, text) VALUES (new.rowid, new.text);
        END
    """)
    conn.commit()

    conn.execute(
        """INSERT INTO artifacts (slug, title, summary, created_at, updated_at)
           VALUES ('quantum-computing', 'Quantum Computing Basics', 'An intro to quantum computing', '2026-01-01', '2026-01-01')"""
    )
    conn.execute(
        """INSERT INTO artifacts (slug, title, summary, created_at, updated_at)
           VALUES ('machine-learning', 'Machine Learning Guide', 'ML fundamentals', '2026-01-01', '2026-01-01')"""
    )
    conn.execute(
        """INSERT INTO artifacts (slug, title, summary, created_at, updated_at)
           VALUES ('distributed-systems', 'Distributed Systems', 'Distributed systems overview', '2026-01-01', '2026-01-01')"""
    )
    conn.commit()

    conn.execute(
        """INSERT INTO chunks (artifact_id, ordinal, text, char_start, char_end, created_at)
           VALUES (1, 0, 'Quantum computing uses qubits which can exist in superposition states unlike classical bits.', 0, 90, '2026-01-01')"""
    )
    conn.execute(
        """INSERT INTO chunks (artifact_id, ordinal, text, char_start, char_end, created_at)
           VALUES (2, 0, 'Machine learning algorithms learn patterns from training data to make predictions.', 0, 80, '2026-01-01')"""
    )
    conn.execute(
        """INSERT INTO chunks (artifact_id, ordinal, text, char_start, char_end, created_at)
           VALUES (3, 0, 'Distributed systems coordinate multiple computers to achieve fault tolerance and scalability.', 0, 92, '2026-01-01')"""
    )
    conn.commit()

    conn.execute(
        "INSERT INTO embeddings (chunk_id, embedding) VALUES (?, ?)",
        (1, _serialize_vector(_make_vector(1.0))),
    )
    conn.execute(
        "INSERT INTO embeddings (chunk_id, embedding) VALUES (?, ?)",
        (2, _serialize_vector(_make_vector(0.5))),
    )
    conn.execute(
        "INSERT INTO embeddings (chunk_id, embedding) VALUES (?, ?)",
        (3, _serialize_vector(_make_vector(0.25))),
    )
    conn.commit()

    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# FTS tests
# ---------------------------------------------------------------------------


def test_fts_returns_matching_chunks(retrieval_db):
    """FTS query for 'quantum' returns the quantum computing chunk."""
    results = fts_search(retrieval_db, "quantum")
    assert len(results) >= 1
    assert results[0].artifact_slug == "quantum-computing"
    assert results[0].artifact_title == "Quantum Computing Basics"
    assert "qubits" in results[0].text
    assert results[0].match_type == "fts"


def test_fts_empty_on_no_match(retrieval_db):
    """Query for text that doesn't exist returns empty list."""
    results = fts_search(retrieval_db, "blockchain")
    assert results == []


def test_fts_bad_query_returns_empty(retrieval_db):
    """Malformed FTS query returns empty list, no exception raised."""
    results = fts_search(retrieval_db, "AND OR NOT")
    assert results == []


# ---------------------------------------------------------------------------
# Vector search tests
# ---------------------------------------------------------------------------


def test_vec_search_returns_ranked_results(retrieval_db):
    """Query embedding [1.0, 0, ...] should rank chunk 1 closest."""
    query_vec = _make_vector(1.0)
    results = vec_search(retrieval_db, query_vec, limit=10)
    assert len(results) == 3
    assert results[0].chunk_id == 1
    assert results[0].score > results[1].score > results[2].score
    assert results[0].match_type == "vec"


def test_vec_search_empty_when_no_embeddings(tmp_path: Path):
    """Empty embeddings table returns empty list."""
    db_path = tmp_path / "manifest.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row

    conn.execute("""
        CREATE TABLE artifacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            tags TEXT NOT NULL DEFAULT '',
            topics TEXT NOT NULL DEFAULT '',
            html_path TEXT,
            md_path TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()

    migrate.apply_migrations(conn, MIGRATIONS_DIR, skip_backup_check=True)

    query_vec = _make_vector(1.0)
    results = vec_search(conn, query_vec, limit=10)
    assert results == []
    conn.close()


# ---------------------------------------------------------------------------
# Hybrid search tests
# ---------------------------------------------------------------------------


def test_hybrid_merges_and_deduplicates(retrieval_db):
    """Same chunk in FTS and vec results appears once with match_type='hybrid'."""
    query_vec = _make_vector(1.0)
    results = hybrid_search(retrieval_db, "quantum", query_vec, limit=5)

    quantum_results = [r for r in results if r.chunk_id == 1]
    assert len(quantum_results) == 1
    assert quantum_results[0].match_type == "hybrid"


def test_hybrid_returns_top_limit(retrieval_db):
    """Insert additional chunks, verify hybrid returns at most `limit` results."""
    for i in range(10):
        retrieval_db.execute(
            """INSERT INTO chunks (artifact_id, ordinal, text, char_start, char_end, created_at)
               VALUES (1, ?, ?, 0, 50, '2026-01-01')""",
            (i + 10, f"Extra chunk number {i} about quantum physics and computing"),
        )
    retrieval_db.commit()

    # Manually populate FTS for new chunks
    rows = retrieval_db.execute("SELECT rowid, text FROM chunks WHERE ordinal >= 10").fetchall()
    for row in rows:
        retrieval_db.execute("INSERT INTO chunks_fts(rowid, text) VALUES (?, ?)", (row[0], row[1]))
    retrieval_db.commit()

    query_vec = _make_vector(0.9)
    results = hybrid_search(retrieval_db, "quantum", query_vec, limit=5)
    assert len(results) <= 5
