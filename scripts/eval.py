"""scripts/eval.py — 10-question retrieval smoke test for Phase C.

Usage:
    uv run scripts/eval.py [--db PATH]

Runs 10 hardcoded questions against hybrid_search, verifying the retrieval
pipeline returns results. Passes if >= 8/10 questions get at least 1 result.
No LLM generation — retrieval only.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.db import default_db_path, load_sqlite_vec
from lib.provider import BedrockProvider
from lib.retrieval import RetrievalResult, hybrid_search

EVAL_QUESTIONS = [
    "What is the transformer architecture?",
    "How does attention work in neural networks?",
    "What is retrieval-augmented generation?",
    "How do large language models handle long contexts?",
    "What are embedding models used for?",
    "How does vector similarity search work?",
    "What is the difference between fine-tuning and prompting?",
    "How are language models evaluated?",
    "What is in-context learning?",
    "How do AI agents use tools?",
]

PASS_THRESHOLD = 8


def corpus_stats(db: sqlite3.Connection) -> tuple[int, int, int]:
    """Return (artifact_count, chunk_count, embedding_count)."""
    artifacts = db.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]
    chunks = db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    try:
        embeddings = db.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
    except Exception:
        embeddings = 0
    return artifacts, chunks, embeddings


def run_eval(
    db: sqlite3.Connection,
    provider,
    questions: list[str] | None = None,
    limit: int = 5,
) -> tuple[list[tuple[str, list[RetrievalResult]]], int, int]:
    """Run eval questions against hybrid_search.

    Returns (results_per_question, passed_count, total_count) where
    results_per_question is a list of (question, results) tuples.
    """
    qs = questions or EVAL_QUESTIONS
    results_per_question: list[tuple[str, list[RetrievalResult]]] = []
    passed = 0

    for question in qs:
        embedding = provider.embed([question], input_type="search_query")[0]
        results = hybrid_search(db, question, embedding, limit=limit)
        results_per_question.append((question, results))
        if len(results) >= 1:
            passed += 1

    return results_per_question, passed, len(qs)


def format_report(
    corpus: tuple[int, int, int],
    results_per_question: list[tuple[str, list[RetrievalResult]]],
    passed: int,
    total: int,
) -> str:
    """Format the eval report as a string."""
    lines = [
        "EvoResearch Phase C — Retrieval Smoke Test",
        f"Corpus: {corpus[0]} artifacts, {corpus[1]} chunks, {corpus[2]} embeddings",
        "",
    ]

    for i, (question, results) in enumerate(results_per_question, 1):
        if results:
            fts_count = sum(1 for r in results if r.match_type == "fts")
            vec_count = sum(1 for r in results if r.match_type == "vec")
            hybrid_count = sum(1 for r in results if r.match_type == "hybrid")
            status = f"PASS — {len(results)} results (fts:{fts_count} vec:{vec_count} hybrid:{hybrid_count})"
        else:
            status = "FAIL — 0 results"
        lines.append(f"Q{i:02d}: {question}")
        lines.append(f"  {status}")

    lines.append("")
    lines.append(f"Results: {passed}/{total} passed")
    if passed >= PASS_THRESHOLD:
        lines.append("Status: PASS")
    else:
        lines.append("Status: FAIL")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="EvoResearch retrieval smoke test")
    parser.add_argument("--db", type=Path, default=None, help="Path to manifest.db")
    args = parser.parse_args(argv)

    db_path = args.db or default_db_path()
    if not db_path.exists():
        print(f"ERROR: DB not found at {db_path}", file=sys.stderr)
        return 1

    try:
        provider = BedrockProvider()
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row
    load_sqlite_vec(conn)

    corpus = corpus_stats(conn)
    results_per_question, passed, total = run_eval(conn, provider, limit=5)
    report = format_report(corpus, results_per_question, passed, total)

    print(report)
    conn.close()

    return 0 if passed >= PASS_THRESHOLD else 1


if __name__ == "__main__":
    sys.exit(main())
