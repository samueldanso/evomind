"""Tests for scripts/embed.py — embedding pipeline with MockProvider."""

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent))

import embed

from tests.test_provider import MockProvider

MIGRATIONS_DIR = Path(__file__).parent.parent / "scripts" / "migrations"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def fresh_db(tmp_path: Path) -> sqlite3.Connection:
    """Fresh DB with migration 002 applied and sample artifacts + chunks."""
    import migrate

    db_path = tmp_path / "manifest.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row

    # Create artifacts table (base schema)
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

    # Apply migration 002
    migrate.apply_migrations(conn, MIGRATIONS_DIR, skip_backup_check=True)

    # Seed 3 artifacts with chunks
    for i in range(3):
        conn.execute(
            """INSERT INTO artifacts (slug, title, summary, created_at, updated_at)
               VALUES (?, ?, ?, '2026-01-01', '2026-01-01')""",
            (f"art-{i}", f"Article {i}", f"Summary {i}"),
        )
    conn.commit()

    # Insert chunks for each artifact (varying counts for batch test)
    chunk_id = 1
    for art_id in range(1, 4):
        for ordinal in range(5):
            conn.execute(
                """INSERT INTO chunks (artifact_id, ordinal, text, char_start, char_end, created_at)
                   VALUES (?, ?, ?, ?, ?, '2026-01-01')""",
                (art_id, ordinal, f"Chunk text for article {art_id} part {ordinal}", 0, 40),
            )
            chunk_id += 1
    conn.commit()

    yield conn
    conn.close()


@pytest.fixture()
def mock_provider() -> MockProvider:
    return MockProvider()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_incremental_embeds_new_chunks(fresh_db, mock_provider):
    """Incremental mode embeds all chunks that have no embeddings."""
    chunks = embed.get_unembedded_chunks(fresh_db)
    assert len(chunks) == 15  # 3 artifacts * 5 chunks each

    count = embed.embed_chunks(fresh_db, chunks, mock_provider)
    assert count == 15

    row = fresh_db.execute("SELECT COUNT(*) FROM embeddings").fetchone()
    assert row[0] == 15


def test_incremental_is_noop_when_all_embedded(fresh_db, mock_provider):
    """Second incremental run embeds 0 chunks."""
    chunks = embed.get_unembedded_chunks(fresh_db)
    embed.embed_chunks(fresh_db, chunks, mock_provider)

    # Second run
    chunks_again = embed.get_unembedded_chunks(fresh_db)
    assert len(chunks_again) == 0

    count = embed.embed_chunks(fresh_db, chunks_again, mock_provider)
    assert count == 0


def test_rebuild_reembeds_all(fresh_db, mock_provider):
    """Rebuild clears and re-embeds — count stays equal to chunk count."""
    # First embed all
    chunks = embed.get_all_chunks(fresh_db)
    embed.embed_chunks(fresh_db, chunks, mock_provider)

    # Clear and re-embed (simulating rebuild without interactive prompt)
    fresh_db.execute("DELETE FROM embeddings")
    fresh_db.commit()

    chunks = embed.get_all_chunks(fresh_db)
    count = embed.embed_chunks(fresh_db, chunks, mock_provider)
    assert count == 15

    row = fresh_db.execute("SELECT COUNT(*) FROM embeddings").fetchone()
    assert row[0] == 15


def test_batch_size_respected(tmp_path: Path):
    """With 130 chunks, MockProvider.embed() is called at least 3 times (batches of 64)."""
    import migrate

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
    conn.execute(
        """INSERT INTO artifacts (slug, title, summary, created_at, updated_at)
           VALUES ('batch-test', 'Batch', 'Test', '2026-01-01', '2026-01-01')"""
    )
    conn.commit()

    migrate.apply_migrations(conn, MIGRATIONS_DIR, skip_backup_check=True)

    # Insert 130 chunks
    for i in range(130):
        conn.execute(
            """INSERT INTO chunks (artifact_id, ordinal, text, char_start, char_end, created_at)
               VALUES (1, ?, ?, 0, 20, '2026-01-01')""",
            (i, f"Chunk number {i}"),
        )
    conn.commit()

    mock = MockProvider()
    chunks = embed.get_unembedded_chunks(conn)
    assert len(chunks) == 130

    embed.embed_chunks(conn, chunks, mock)

    # 130 / 64 = 2.03 → 3 batches (64 + 64 + 2)
    assert len(mock.embed_calls) >= 3
    assert mock.embed_calls[0].__len__() == 64
    assert mock.embed_calls[1].__len__() == 64
    assert mock.embed_calls[2].__len__() == 2

    conn.close()
