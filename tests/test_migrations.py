"""Tests for scripts/migrate.py and scripts/migrations/002_phase_c.sql."""

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import migrate

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MIGRATIONS_DIR = Path(__file__).parent.parent / "scripts" / "migrations"


def open_fresh_db(tmp_path: Path) -> sqlite3.Connection:
    """Open an in-memory-like fresh DB at a tmp path (avoids real vault)."""
    db_path = tmp_path / "test_manifest.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def seed_artifacts_table(conn: sqlite3.Connection) -> int:
    """Seed the artifacts table so FK references in chunks are valid."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS artifacts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            slug        TEXT NOT NULL UNIQUE,
            title       TEXT NOT NULL,
            summary     TEXT NOT NULL,
            tags        TEXT NOT NULL DEFAULT '',
            topics      TEXT NOT NULL DEFAULT '',
            html_path   TEXT,
            md_path     TEXT,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL,
            archived    INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.execute("""
        INSERT INTO artifacts (slug, title, summary, tags, topics, created_at, updated_at)
        VALUES ('test-slug', 'Test', 'Summary', '', '', '2026-01-01', '2026-01-01')
    """)
    conn.commit()
    row = conn.execute("SELECT id FROM artifacts WHERE slug = 'test-slug'").fetchone()
    return row[0]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestApplyMigration002:
    """Apply migration 002 to a fresh DB — verify all tables exist."""

    def test_all_tables_exist_after_migration(self, tmp_path: Path) -> None:
        conn = open_fresh_db(tmp_path)
        seed_artifacts_table(conn)
        migrate.apply_migrations(conn, MIGRATIONS_DIR, skip_backup_check=True)

        table_names = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        for expected in ("chunks", "claims", "claim_sources", "migrations"):
            assert expected in table_names, f"Table '{expected}' missing after migration 002"

    def test_embeddings_virtual_table_exists(self, tmp_path: Path) -> None:
        conn = open_fresh_db(tmp_path)
        seed_artifacts_table(conn)
        migrate.apply_migrations(conn, MIGRATIONS_DIR, skip_backup_check=True)

        # sqlite-vec creates shadow tables; check the virtual table name is registered
        row = conn.execute("SELECT name FROM sqlite_master WHERE name = 'embeddings'").fetchone()
        assert row is not None, "Virtual table 'embeddings' missing after migration 002"

    def test_migrations_table_records_version(self, tmp_path: Path) -> None:
        conn = open_fresh_db(tmp_path)
        seed_artifacts_table(conn)
        migrate.apply_migrations(conn, MIGRATIONS_DIR, skip_backup_check=True)

        row = conn.execute("SELECT version FROM migrations WHERE version = 2").fetchone()
        assert row is not None, "Migration version 2 not recorded in migrations table"


class TestIdempotency:
    """Applying the migration twice must not raise."""

    def test_apply_twice_no_error(self, tmp_path: Path) -> None:
        conn = open_fresh_db(tmp_path)
        seed_artifacts_table(conn)
        migrate.apply_migrations(conn, MIGRATIONS_DIR, skip_backup_check=True)
        # Second application must be a no-op — not raise
        migrate.apply_migrations(conn, MIGRATIONS_DIR, skip_backup_check=True)


class TestCascadeDelete:
    """ON DELETE CASCADE: deleting an artifact removes its chunks."""

    def test_cascade_delete_chunks(self, tmp_path: Path) -> None:
        conn = open_fresh_db(tmp_path)
        artifact_id = seed_artifacts_table(conn)
        migrate.apply_migrations(conn, MIGRATIONS_DIR, skip_backup_check=True)
        conn.execute("PRAGMA foreign_keys = ON")

        conn.execute(
            """
            INSERT INTO chunks (artifact_id, ordinal, text, char_start, char_end, created_at)
            VALUES (?, 0, 'Hello world', 0, 11, '2026-01-01T00:00:00Z')
        """,
            (artifact_id,),
        )
        conn.commit()

        count = conn.execute(
            "SELECT COUNT(*) FROM chunks WHERE artifact_id = ?", (artifact_id,)
        ).fetchone()[0]
        assert count == 1

        conn.execute("DELETE FROM artifacts WHERE id = ?", (artifact_id,))
        conn.commit()

        count_after = conn.execute(
            "SELECT COUNT(*) FROM chunks WHERE artifact_id = ?", (artifact_id,)
        ).fetchone()[0]
        assert count_after == 0, "Chunk rows not removed by ON DELETE CASCADE"


class TestBackupCheck:
    """--skip-backup-check suppresses the backup check error."""

    def test_skip_backup_check_flag_accepted(self, tmp_path: Path) -> None:
        conn = open_fresh_db(tmp_path)
        seed_artifacts_table(conn)
        # Should not raise even with no .bak file present
        migrate.apply_migrations(conn, MIGRATIONS_DIR, skip_backup_check=True)

    def test_backup_check_raises_when_bak_missing(self, tmp_path: Path) -> None:
        db_path = tmp_path / "manifest.db"
        db_path.write_text("")  # create a fake db file
        with pytest.raises(SystemExit):
            migrate.check_backup(db_path)
