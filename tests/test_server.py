"""Tests for server/ — FastAPI chat, health, and agent endpoints."""

import sqlite3
import struct
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent))

import migrate

from core.governance import audit
from core.llm.bedrock import ChatResponse
from core.runtime.contracts import AgentRun, ToolCallRecord

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
    """Fresh DB with migrations, artifacts, chunks, and embeddings."""
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

    from fastapi import FastAPI

    from server.routes.agent import router as agent_router
    from server.routes.chat import router as chat_router

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
    test_app.include_router(chat_router)
    test_app.include_router(agent_router)

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


def _mock_research_run() -> AgentRun:
    return AgentRun(
        id=1,
        agent_type="research_agent",
        task_input={"task_type": "research", "topic": "Test", "mode": "concept", "context": None},
        status="complete",
        output={"artifact_slug": "test", "artifact_id": 1, "summary": "test summary"},
        error=None,
        tool_calls=[],
        cost_tokens=100,
        cost_usd=0.001,
        started_at="2026-06-08T00:00:00Z",
        finished_at="2026-06-08T00:01:00Z",
    )


def test_agent_dispatch_research(chat_db: sqlite3.Connection):
    from starlette.testclient import TestClient

    test_app = _create_test_app(chat_db)

    with patch("server.routes.agent.dispatch", return_value=_mock_research_run()):
        with TestClient(test_app, raise_server_exceptions=False) as client:
            response = client.post("/api/agent", json={
                "task_type": "research",
                "topic": "Test Topic",
                "mode": "concept",
            })

    assert response.status_code == 200
    data = response.json()
    assert "run" in data
    assert data["run"]["status"] == "complete"
    assert data["run"]["id"] == 1
    assert data["teach_run"] is None


def test_agent_dispatch_invalid_task_type(chat_db: sqlite3.Connection):
    from starlette.testclient import TestClient

    test_app = _create_test_app(chat_db)

    with TestClient(test_app, raise_server_exceptions=False) as client:
        response = client.post("/api/agent", json={
            "task_type": "invalid",
            "topic": "Test",
        })

    assert response.status_code == 422
    assert "error" in response.json()


def test_agent_dispatch_missing_topic(chat_db: sqlite3.Connection):
    from starlette.testclient import TestClient

    test_app = _create_test_app(chat_db)

    with TestClient(test_app, raise_server_exceptions=False) as client:
        response = client.post("/api/agent", json={
            "task_type": "research",
        })

    assert response.status_code == 422
    assert "error" in response.json()


def test_agent_get_run(chat_db: sqlite3.Connection):
    from starlette.testclient import TestClient

    test_app = _create_test_app(chat_db)
    run_id = audit.create_run(chat_db, "research_agent", {"topic": "Test"})

    with TestClient(test_app, raise_server_exceptions=False) as client:
        response = client.get(f"/api/agent/{run_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["run"]["id"] == run_id


def test_agent_get_run_not_found(chat_db: sqlite3.Connection):
    from starlette.testclient import TestClient

    test_app = _create_test_app(chat_db)

    with TestClient(test_app, raise_server_exceptions=False) as client:
        response = client.get("/api/agent/9999")

    assert response.status_code == 404


def test_agent_post_message(chat_db: sqlite3.Connection):
    from starlette.testclient import TestClient

    test_app = _create_test_app(chat_db)
    run_id = audit.create_run(chat_db, "teaching_agent", {"topic": "Test"})

    with TestClient(test_app, raise_server_exceptions=False) as client:
        response = client.post(f"/api/agent/{run_id}/message", json={"content": "My answer"})

    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert data["status"] == "teaching"


def test_agent_list_runs(chat_db: sqlite3.Connection):
    from starlette.testclient import TestClient

    test_app = _create_test_app(chat_db)
    audit.create_run(chat_db, "research_agent", {"topic": "One"})
    audit.create_run(chat_db, "teaching_agent", {"topic": "Two"})

    with TestClient(test_app, raise_server_exceptions=False) as client:
        response = client.get("/api/agent/runs")

    assert response.status_code == 200
    data = response.json()
    assert "runs" in data
    assert len(data["runs"]) == 2


def test_chat_still_works_after_restructure(chat_db: sqlite3.Connection):
    from starlette.testclient import TestClient

    test_app = _create_test_app(chat_db)

    with TestClient(test_app, raise_server_exceptions=False) as client:
        response = client.post("/chat", json={"query": "machine learning"})

    assert response.status_code == 200
    assert "answer" in response.json()
