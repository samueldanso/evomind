"""Tests for server.py — FastAPI chat + health endpoints."""

import sqlite3
import struct
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent))

import migrate

from core.llm.bedrock import ChatResponse

MIGRATIONS_DIR = Path(__file__).parent.parent / "scripts" / "migrations"
EMBEDDING_DIM = 1024


def _serialize_vector(vector: list[float]) -> bytes:
    return struct.pack(f"{len(vector)}f", *vector)


def _make_vector(first_val: float) -> list[float]:
    vec = [0.0] * EMBEDDING_DIM
    vec[0] = first_val
    return vec


@pytest.fixture()
def chat_db(tmp_path: Path) -> sqlite3.Connection:
    """Fresh DB with migration 002, artifacts, chunks, and embeddings."""
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
    conn.commit()

    conn.execute(
        """INSERT INTO artifacts (slug, title, summary, created_at, updated_at)
           VALUES ('quantum-computing', 'Quantum Computing Basics', 'An intro to quantum computing', '2026-01-01', '2026-01-01')"""
    )
    conn.execute(
        """INSERT INTO artifacts (slug, title, summary, created_at, updated_at)
           VALUES ('machine-learning', 'Machine Learning Guide', 'ML fundamentals', '2026-01-01', '2026-01-01')"""
    )
    conn.commit()

    conn.execute(
        """INSERT INTO chunks (artifact_id, ordinal, text, char_start, char_end, created_at)
           VALUES (1, 0, 'Quantum computing uses qubits which can exist in superposition states.', 0, 70, '2026-01-01')"""
    )
    conn.execute(
        """INSERT INTO chunks (artifact_id, ordinal, text, char_start, char_end, created_at)
           VALUES (2, 0, 'Machine learning algorithms learn patterns from training data.', 0, 62, '2026-01-01')"""
    )
    conn.commit()

    try:
        import sqlite_vec  # type: ignore[import-untyped]

        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)

        vec1 = _make_vector(0.9)
        vec2 = _make_vector(0.3)
        conn.execute(
            "INSERT INTO embeddings (chunk_id, embedding) VALUES (?, ?)",
            (1, _serialize_vector(vec1)),
        )
        conn.execute(
            "INSERT INTO embeddings (chunk_id, embedding) VALUES (?, ?)",
            (2, _serialize_vector(vec2)),
        )
        conn.commit()
    except Exception:
        pass

    return conn


@pytest.fixture()
def chat_db_no_embeddings(tmp_path: Path) -> sqlite3.Connection:
    """DB with chunks but no embeddings."""
    db_path = tmp_path / "manifest_empty.db"
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
    conn.commit()

    conn.execute(
        """INSERT INTO artifacts (slug, title, summary, created_at, updated_at)
           VALUES ('test-article', 'Test Article', 'A test', '2026-01-01', '2026-01-01')"""
    )
    conn.commit()
    conn.execute(
        """INSERT INTO chunks (artifact_id, ordinal, text, char_start, char_end, created_at)
           VALUES (1, 0, 'Some test content about testing things.', 0, 39, '2026-01-01')"""
    )
    conn.commit()

    return conn


def _mock_embed(texts: list[str], input_type: str = "search_query") -> list[list[float]]:
    return [[0.1] * EMBEDDING_DIM for _ in texts]


def _mock_chat(messages, context_chunks):
    return ChatResponse(content="test answer", citations=[])


def _create_test_app(db: sqlite3.Connection):
    """Create a test app with mocked providers pointing at the given DB."""
    from contextlib import asynccontextmanager
    from unittest.mock import MagicMock

    from fastapi import FastAPI

    from server import chat, health

    @asynccontextmanager
    async def test_lifespan(app: FastAPI):
        app.state.db = db
        app.state.db_path = ":memory:"
        app.state.startup_error = None

        provider = MagicMock()
        provider.embed = _mock_embed
        provider.chat = _mock_chat

        app.state.provider = provider
        yield

    test_app = FastAPI(lifespan=test_lifespan)
    test_app.get("/health")(health)
    test_app.post("/chat")(chat)

    return test_app


def test_health_returns_ok(chat_db: sqlite3.Connection):
    from starlette.testclient import TestClient

    test_app = _create_test_app(chat_db)

    with TestClient(test_app, raise_server_exceptions=False) as client:
        response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["chunk_count"] >= 0


def test_chat_returns_answer_and_sources(chat_db: sqlite3.Connection):
    from starlette.testclient import TestClient

    test_app = _create_test_app(chat_db)

    with TestClient(test_app, raise_server_exceptions=False) as client:
        response = client.post("/chat", json={"query": "quantum computing"})

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["answer"] == "test answer"
    assert "sources" in data
    assert isinstance(data["sources"], list)


def test_chat_empty_db_returns_empty_sources(chat_db_no_embeddings: sqlite3.Connection):
    from starlette.testclient import TestClient

    test_app = _create_test_app(chat_db_no_embeddings)

    with TestClient(test_app, raise_server_exceptions=False) as client:
        response = client.post("/chat", json={"query": "nonexistent topic xyz"})

    assert response.status_code == 200
    data = response.json()
    assert data["sources"] == []
