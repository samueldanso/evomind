"""Tests for scripts/eval.py — retrieval smoke test logic."""

import sqlite3
import struct
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent))

import migrate
from lib.provider import ChatMessage, ChatResponse
from lib.retrieval import RetrievalResult
from scripts.eval import PASS_THRESHOLD, corpus_stats, format_report, run_eval

MIGRATIONS_DIR = Path(__file__).parent.parent / "scripts" / "migrations"
EMBEDDING_DIM = 1536


class MockProvider:
    """Deterministic mock provider for eval tests — no real API calls."""

    def __init__(self, return_embeddings: bool = True) -> None:
        self._return_embeddings = return_embeddings
        self.embed_calls: list[list[str]] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.embed_calls.append(texts)
        return [[0.1] * EMBEDDING_DIM for _ in texts]

    def chat(self, messages: list[ChatMessage], context_chunks: list[str]) -> ChatResponse:
        return ChatResponse(content="Mock response.")


def _serialize_vector(vector: list[float]) -> bytes:
    return struct.pack(f"{len(vector)}f", *vector)


SAMPLE_TEXTS = [
    "The transformer architecture uses self-attention mechanisms to process sequences in parallel, enabling efficient training on large datasets.",
    "Attention in neural networks allows models to focus on relevant parts of the input when producing each output element.",
    "Retrieval-augmented generation combines a retriever that finds relevant documents with a generator that produces answers grounded in those documents.",
    "Large language models handle long contexts through techniques like sliding window attention, sparse attention patterns, and hierarchical processing.",
    "Embedding models convert text into dense vector representations that capture semantic meaning, enabling similarity search and clustering.",
]


@pytest.fixture()
def eval_db(tmp_path: Path) -> sqlite3.Connection:
    """Fresh DB with migration 002, 5 artifacts + chunks + embeddings."""
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

    slugs = [
        ("transformer-arch", "Transformer Architecture"),
        ("attention-mechanisms", "Attention in Neural Networks"),
        ("rag-overview", "Retrieval-Augmented Generation"),
        ("long-context-llms", "LLMs and Long Contexts"),
        ("embedding-models", "Embedding Models"),
    ]

    for i, (slug, title) in enumerate(slugs, 1):
        conn.execute(
            """INSERT INTO artifacts (id, slug, title, summary, created_at, updated_at)
               VALUES (?, ?, ?, ?, '2026-01-01', '2026-01-01')""",
            (i, slug, title, f"Summary for {title}"),
        )
    conn.commit()

    for i, text in enumerate(SAMPLE_TEXTS, 1):
        conn.execute(
            """INSERT INTO chunks (artifact_id, ordinal, text, char_start, char_end, created_at)
               VALUES (?, 0, ?, 0, ?, '2026-01-01')""",
            (i, text, len(text)),
        )
    conn.commit()

    embedding_vec = [0.1] * EMBEDDING_DIM
    blob = _serialize_vector(embedding_vec)
    for chunk_id in range(1, 6):
        conn.execute(
            "INSERT INTO embeddings (chunk_id, embedding) VALUES (?, ?)",
            (chunk_id, blob),
        )
    conn.commit()

    yield conn
    conn.close()


@pytest.fixture()
def empty_eval_db(tmp_path: Path) -> sqlite3.Connection:
    """DB with migration 002, artifacts and chunks but NO embeddings."""
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
    conn.commit()

    conn.execute(
        """INSERT INTO artifacts (slug, title, summary, created_at, updated_at)
           VALUES ('empty-artifact', 'Empty', 'No content', '2026-01-01', '2026-01-01')"""
    )
    conn.commit()

    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_eval_passes_when_retrieval_works(eval_db):
    """All 10 questions return >= 1 result when corpus has matching content."""
    provider = MockProvider()
    results_per_question, passed, total = run_eval(eval_db, provider, limit=5)

    assert total == 10
    assert passed == 10
    for question, results in results_per_question:
        assert len(results) >= 1, f"Expected results for: {question}"


def test_eval_fails_when_no_embeddings(empty_eval_db):
    """0 results per question when embeddings table is empty and FTS has no matching text."""
    provider = MockProvider()
    results_per_question, passed, total = run_eval(empty_eval_db, provider, limit=5)

    assert total == 10
    assert passed == 0
    for question, results in results_per_question:
        assert len(results) == 0


def test_eval_partial_pass(eval_db):
    """8 questions hit, 2 miss — passes the >= 8 threshold."""

    class PartialProvider:
        """Returns zero-vector embeddings so only FTS matches contribute."""

        def embed(self, texts: list[str]) -> list[list[float]]:
            return [[0.0] * EMBEDDING_DIM for _ in texts]

        def chat(self, messages, context_chunks):
            return ChatResponse(content="Mock.")

    eval_db.execute("DELETE FROM embeddings")
    eval_db.commit()

    questions = [
        "transformer",
        "attention",
        "retrieval",
        "sequences",
        "embedding",
        "documents",
        "parallel",
        "semantic",
        "unique-nonexistent-term-xyz-12345",
        "another-nonexistent-term-abc-67890",
    ]

    provider = PartialProvider()
    results_per_question, passed, total = run_eval(
        eval_db, provider, questions=questions, limit=5
    )

    assert total == 10
    assert passed >= 8
    assert passed < total

    corpus = corpus_stats(eval_db)
    report = format_report(corpus, results_per_question, passed, total)
    assert "Status: PASS" in report


def test_corpus_stats(eval_db):
    """corpus_stats returns correct counts."""
    artifacts, chunks, embeddings = corpus_stats(eval_db)
    assert artifacts == 5
    assert chunks == 5
    assert embeddings == 5


def test_format_report_pass():
    """Report shows PASS when threshold met."""
    results = [
        ("Q1?", [RetrievalResult(1, "slug", "Title", "text", 0.9, "fts")]),
    ] * 10
    report = format_report((5, 10, 10), results, 10, 10)
    assert "10/10 passed" in report
    assert "Status: PASS" in report


def test_format_report_fail():
    """Report shows FAIL when below threshold."""
    results = [("Q1?", [])] * 10
    report = format_report((5, 10, 0), results, 0, 10)
    assert "0/10 passed" in report
    assert "Status: FAIL" in report
