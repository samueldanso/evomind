"""Tests for scripts/ingest.py — 100% coverage required."""

import json
import sqlite3
import sys
from pathlib import Path

import pytest

# Allow importing scripts/ingest.py without package install
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import ingest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def store(tmp_path: Path) -> Path:
    s = tmp_path / "research"
    ingest.bootstrap_store(s)
    return s


@pytest.fixture()
def db(store: Path) -> sqlite3.Connection:
    conn = ingest.init_db(store / "manifest.db")
    yield conn
    conn.close()


@pytest.fixture()
def sample_html(tmp_path: Path) -> Path:
    p = tmp_path / "article.html"
    p.write_text("<html><body>Test content</body></html>", encoding="utf-8")
    return p


def _make_artifact(store: Path, html_path: str, **overrides) -> ingest.Artifact:
    now = "2026-01-01T00:00:00Z"
    defaults = dict(
        slug="test-slug",
        title="Test Title",
        summary="A test summary.",
        tags="ai,python",
        topics="llm,infra",
        html_path=html_path,
        md_path=None,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return ingest.Artifact(**defaults)


# ---------------------------------------------------------------------------
# T2 — get_store_path + bootstrap_store
# ---------------------------------------------------------------------------


def test_get_store_path_default():
    path = ingest.get_store_path()
    assert "Research" in str(path)
    assert str(Path.home()) in str(path)


def test_get_store_path_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("EVO_RESEARCH_STORE", str(tmp_path / "custom"))
    path = ingest.get_store_path()
    assert path == tmp_path / "custom"


def test_bootstrap_store_creates_subdirs(tmp_path):
    store = tmp_path / "vault"
    ingest.bootstrap_store(store)
    assert (store / "html").is_dir()
    assert (store / "summaries").is_dir()


def test_bootstrap_store_idempotent(tmp_path):
    store = tmp_path / "vault"
    ingest.bootstrap_store(store)
    ingest.bootstrap_store(store)  # second call should not raise
    assert (store / "html").is_dir()


# ---------------------------------------------------------------------------
# T3 — init_db schema + triggers
# ---------------------------------------------------------------------------


def test_init_db_creates_tables(store):
    conn = ingest.init_db(store / "manifest.db")
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table', 'shadow')"
        )
    }
    assert "artifacts" in tables
    conn.close()


def test_init_db_creates_fts_table(store):
    conn = ingest.init_db(store / "manifest.db")
    # FTS virtual table appears in sqlite_master
    names = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    assert "artifacts_fts" in names
    conn.close()


def test_init_db_creates_triggers(store):
    conn = ingest.init_db(store / "manifest.db")
    triggers = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger'"
        )
    }
    assert {"artifacts_ai", "artifacts_au", "artifacts_ad"} <= triggers
    conn.close()


def test_init_db_idempotent(store):
    ingest.init_db(store / "manifest.db").close()
    conn = ingest.init_db(store / "manifest.db")  # should not raise
    conn.close()


def test_init_db_row_factory(store):
    conn = ingest.init_db(store / "manifest.db")
    assert conn.row_factory is sqlite3.Row
    conn.close()


# ---------------------------------------------------------------------------
# T4 — save_artifact + write_companion_md
# ---------------------------------------------------------------------------


def test_save_artifact_inserts_row(db, store, sample_html):
    artifact = _make_artifact(store, str(sample_html))
    ingest.save_artifact(db, store, artifact)
    row = db.execute("SELECT * FROM artifacts WHERE slug=?", ("test-slug",)).fetchone()
    assert row is not None
    assert row["title"] == "Test Title"


def test_save_artifact_upsert_updates_fields(db, store, sample_html):
    artifact = _make_artifact(store, str(sample_html))
    ingest.save_artifact(db, store, artifact)

    updated = _make_artifact(
        store, str(sample_html), title="Updated Title", updated_at="2026-06-01T00:00:00Z"
    )
    ingest.save_artifact(db, store, updated)

    rows = db.execute("SELECT * FROM artifacts WHERE slug=?", ("test-slug",)).fetchall()
    assert len(rows) == 1
    assert rows[0]["title"] == "Updated Title"


def test_save_artifact_fts_searchable_after_insert(db, store, sample_html):
    artifact = _make_artifact(store, str(sample_html), title="Unique Flamingo Research")
    ingest.save_artifact(db, store, artifact)
    results = ingest.search_artifacts(db, "Flamingo")
    assert len(results) == 1
    assert results[0]["title"] == "Unique Flamingo Research"


def test_write_companion_md_creates_file(store, sample_html):
    artifact = _make_artifact(store, str(sample_html))
    md_path = ingest.write_companion_md(store, artifact)
    assert md_path.exists()
    content = md_path.read_text()
    assert "Test Title" in content
    assert "test-slug" in content
    assert "ai" in content


def test_write_companion_md_path(store, sample_html):
    artifact = _make_artifact(store, str(sample_html), slug="my-slug")
    md_path = ingest.write_companion_md(store, artifact)
    assert md_path == store / "summaries" / "my-slug.md"


# ---------------------------------------------------------------------------
# T5 — search_artifacts FTS
# ---------------------------------------------------------------------------


def test_search_returns_matches(db, store, sample_html):
    a1 = _make_artifact(store, str(sample_html), slug="alpha", title="Alpha Article")
    a2 = _make_artifact(store, str(sample_html), slug="beta", title="Beta Article")
    ingest.save_artifact(db, store, a1)
    ingest.save_artifact(db, store, a2)

    results = ingest.search_artifacts(db, "Alpha")
    assert len(results) == 1
    assert results[0]["slug"] == "alpha"


def test_search_empty_result(db):
    results = ingest.search_artifacts(db, "nonexistent-xyz-abc")
    assert results == []


def test_search_by_tags(db, store, sample_html):
    artifact = _make_artifact(store, str(sample_html), tags="bedrock,agentcore")
    ingest.save_artifact(db, store, artifact)
    results = ingest.search_artifacts(db, "agentcore")
    assert len(results) == 1


def test_search_by_topics(db, store, sample_html):
    artifact = _make_artifact(store, str(sample_html), topics="kubernetes,infra")
    ingest.save_artifact(db, store, artifact)
    results = ingest.search_artifacts(db, "kubernetes")
    assert len(results) == 1


def test_fts_delete_trigger(db, store, sample_html):
    artifact = _make_artifact(store, str(sample_html), title="Delete Me Research")
    ingest.save_artifact(db, store, artifact)
    assert len(ingest.search_artifacts(db, "Delete")) == 1

    db.execute("DELETE FROM artifacts WHERE slug=?", ("test-slug",))
    db.commit()
    assert ingest.search_artifacts(db, "Delete") == []


def test_fts_update_trigger(db, store, sample_html):
    # Use a direct UPDATE to actually fire the artifacts_au trigger.
    # save_artifact uses ON CONFLICT DO UPDATE which fires the AI trigger, not AU.
    artifact = _make_artifact(store, str(sample_html), title="Original Title Here")
    ingest.save_artifact(db, store, artifact)

    db.execute(
        "UPDATE artifacts SET title=?, updated_at=? WHERE slug=?",
        ("Revised Title Content", "2026-06-01T00:00:00Z", "test-slug"),
    )
    db.commit()

    assert ingest.search_artifacts(db, "Revised") != []
    assert ingest.search_artifacts(db, "Original") == []


# ---------------------------------------------------------------------------
# T6 — list_artifacts
# ---------------------------------------------------------------------------


def test_list_empty_db(db):
    assert ingest.list_artifacts(db) == []


def test_list_returns_all(db, store, sample_html):
    for i, slug in enumerate(["first", "second", "third"]):
        a = _make_artifact(
            store,
            str(sample_html),
            slug=slug,
            title=f"Title {i}",
            created_at=f"2026-0{i+1}-01T00:00:00Z",
            updated_at=f"2026-0{i+1}-01T00:00:00Z",
        )
        ingest.save_artifact(db, store, a)

    results = ingest.list_artifacts(db)
    assert len(results) == 3


def test_list_ordered_newest_first(db, store, sample_html):
    for slug, created in [
        ("old", "2025-01-01T00:00:00Z"),
        ("new", "2026-01-01T00:00:00Z"),
    ]:
        a = _make_artifact(
            store,
            str(sample_html),
            slug=slug,
            created_at=created,
            updated_at=created,
        )
        ingest.save_artifact(db, store, a)

    results = ingest.list_artifacts(db)
    assert results[0]["slug"] == "new"
    assert results[1]["slug"] == "old"


# ---------------------------------------------------------------------------
# T7 — cmd_ingest end-to-end + error paths
# ---------------------------------------------------------------------------


def test_cmd_ingest_copies_html(monkeypatch, tmp_path, sample_html):
    store = tmp_path / "vault"
    monkeypatch.setenv("EVO_RESEARCH_STORE", str(store))

    args = _build_ingest_args(sample_html)
    ingest.cmd_ingest(args)

    html_files = list((store / "html").glob("*.html"))
    assert len(html_files) == 1
    assert "test-slug" in html_files[0].name


def test_cmd_ingest_writes_md(monkeypatch, tmp_path, sample_html):
    store = tmp_path / "vault"
    monkeypatch.setenv("EVO_RESEARCH_STORE", str(store))

    args = _build_ingest_args(sample_html)
    ingest.cmd_ingest(args)

    md = store / "summaries" / "test-slug.md"
    assert md.exists()


def test_cmd_ingest_writes_db(monkeypatch, tmp_path, sample_html):
    store = tmp_path / "vault"
    monkeypatch.setenv("EVO_RESEARCH_STORE", str(store))

    args = _build_ingest_args(sample_html)
    ingest.cmd_ingest(args)

    conn = sqlite3.connect(str(store / "manifest.db"))
    row = conn.execute("SELECT * FROM artifacts WHERE slug=?", ("test-slug",)).fetchone()
    conn.close()
    assert row is not None


def test_cmd_ingest_missing_html_exits(monkeypatch, tmp_path):
    store = tmp_path / "vault"
    monkeypatch.setenv("EVO_RESEARCH_STORE", str(store))

    args = _build_ingest_args(Path("/nonexistent/path.html"))
    with pytest.raises(SystemExit) as exc_info:
        ingest.cmd_ingest(args)
    assert exc_info.value.code == 1


def test_cmd_search_output(monkeypatch, tmp_path, sample_html, capsys):
    store = tmp_path / "vault"
    monkeypatch.setenv("EVO_RESEARCH_STORE", str(store))

    # Seed via ingest; drain capsys so ingest stdout doesn't bleed into parse
    ingest.cmd_ingest(_build_ingest_args(sample_html, title="Searchable Item"))
    capsys.readouterr()

    args = _build_search_args("Searchable")
    ingest.cmd_search(args)

    out = capsys.readouterr().out
    data = json.loads(out)
    assert len(data) == 1
    assert data[0]["title"] == "Searchable Item"


def test_cmd_search_no_results(monkeypatch, tmp_path, capsys):
    store = tmp_path / "vault"
    monkeypatch.setenv("EVO_RESEARCH_STORE", str(store))
    ingest.bootstrap_store(store)

    args = _build_search_args("nothing-here")
    ingest.cmd_search(args)

    out = capsys.readouterr().out
    assert json.loads(out) == []


def test_cmd_list_output(monkeypatch, tmp_path, sample_html, capsys):
    store = tmp_path / "vault"
    monkeypatch.setenv("EVO_RESEARCH_STORE", str(store))

    ingest.cmd_ingest(_build_ingest_args(sample_html))
    capsys.readouterr()  # drain ingest stdout before parsing list output

    args = type("Args", (), {"list": True})()
    ingest.cmd_list(args)

    out = capsys.readouterr().out
    data = json.loads(out)
    assert len(data) == 1


def test_cmd_list_empty(monkeypatch, tmp_path, capsys):
    store = tmp_path / "vault"
    monkeypatch.setenv("EVO_RESEARCH_STORE", str(store))
    ingest.bootstrap_store(store)

    args = type("Args", (), {"list": True})()
    ingest.cmd_list(args)

    out = capsys.readouterr().out
    assert json.loads(out) == []


# ---------------------------------------------------------------------------
# Parser + main() tests
# ---------------------------------------------------------------------------


def test_build_parser_returns_parser():
    parser = ingest.build_parser()
    assert parser is not None


def test_main_list(monkeypatch, tmp_path, capsys):
    store = tmp_path / "vault"
    monkeypatch.setenv("EVO_RESEARCH_STORE", str(store))
    ingest.bootstrap_store(store)
    monkeypatch.setattr(sys, "argv", ["ingest.py", "--list"])
    ingest.main()
    out = capsys.readouterr().out
    assert json.loads(out) == []


def test_main_search(monkeypatch, tmp_path, capsys):
    store = tmp_path / "vault"
    monkeypatch.setenv("EVO_RESEARCH_STORE", str(store))
    ingest.bootstrap_store(store)
    monkeypatch.setattr(sys, "argv", ["ingest.py", "--search", "query"])
    ingest.main()
    out = capsys.readouterr().out
    assert json.loads(out) == []


def test_main_html_missing_required_args(monkeypatch, tmp_path, sample_html):
    store = tmp_path / "vault"
    monkeypatch.setenv("EVO_RESEARCH_STORE", str(store))
    monkeypatch.setattr(
        sys, "argv", ["ingest.py", "--html", str(sample_html), "--title", "T"]
    )
    with pytest.raises(SystemExit):
        ingest.main()


def test_main_empty_search_exits(monkeypatch, tmp_path):
    store = tmp_path / "vault"
    monkeypatch.setenv("EVO_RESEARCH_STORE", str(store))
    monkeypatch.setattr(sys, "argv", ["ingest.py", "--search", "   "])
    with pytest.raises(SystemExit):
        ingest.main()


def test_main_ingest(monkeypatch, tmp_path, sample_html, capsys):
    store = tmp_path / "vault"
    monkeypatch.setenv("EVO_RESEARCH_STORE", str(store))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ingest.py",
            "--html", str(sample_html),
            "--title", "My Title",
            "--slug", "my-slug",
            "--tags", "a,b",
            "--topics", "x,y",
            "--summary", "A summary.",
        ],
    )
    ingest.main()
    out = capsys.readouterr().out
    assert "my-slug" in out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_ingest_args(html_path: Path, **overrides) -> object:
    defaults = dict(
        html=str(html_path),
        title="Test Title",
        slug="test-slug",
        tags="ai,python",
        topics="llm,infra",
        summary="A test summary.",
    )
    defaults.update(overrides)
    return type("Args", (), defaults)()


def _build_search_args(query: str) -> object:
    return type("Args", (), {"search": query})()


# ---------------------------------------------------------------------------
# T3 — chunk_and_store integration
# ---------------------------------------------------------------------------


def _make_artifact_dc(store: Path, html_path: str, **overrides) -> "ingest.Artifact":
    """Build a real Artifact dataclass instance for chunk_and_store tests."""
    now = "2026-01-01T00:00:00Z"
    defaults = dict(
        slug="test-slug",
        title="Test Title",
        summary="A test summary.",
        tags="ai,python",
        topics="llm,infra",
        html_path=html_path,
        md_path=None,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return ingest.Artifact(**defaults)


def test_chunks_created_after_ingest(store: Path, db: sqlite3.Connection) -> None:
    """chunk_and_store writes > 0 chunk rows for a real HTML artifact."""
    html_path = store / "html" / "article.html"
    html_path.write_text(
        "<html><body><p>" + ("This is a sentence. " * 60) + "</p></body></html>",
        encoding="utf-8",
    )
    artifact = _make_artifact_dc(store, str(html_path))
    ingest.save_artifact(db, store, artifact)
    row = db.execute("SELECT id FROM artifacts WHERE slug = ?", (artifact.slug,)).fetchone()
    artifact_id = row[0]

    n = ingest.chunk_and_store(db, artifact_id, html_path)

    assert n > 0, "Expected at least one chunk after ingest"
    count = db.execute(
        "SELECT COUNT(*) FROM chunks WHERE artifact_id = ?", (artifact_id,)
    ).fetchone()[0]
    assert count == n


def test_reingest_updates_chunks_not_duplicate(
    store: Path, db: sqlite3.Connection
) -> None:
    """Re-ingesting the same slug replaces chunks, does not double them."""
    html_path = store / "html" / "dup.html"
    html_path.write_text(
        "<html><body><p>" + ("Sentence number one. " * 60) + "</p></body></html>",
        encoding="utf-8",
    )
    artifact = _make_artifact_dc(store, str(html_path))
    ingest.save_artifact(db, store, artifact)
    artifact_id = db.execute("SELECT id FROM artifacts WHERE slug = ?", (artifact.slug,)).fetchone()[0]

    n_first = ingest.chunk_and_store(db, artifact_id, html_path)
    # Ingest again — same artifact_id, same HTML
    n_second = ingest.chunk_and_store(db, artifact_id, html_path)

    count = db.execute(
        "SELECT COUNT(*) FROM chunks WHERE artifact_id = ?", (artifact_id,)
    ).fetchone()[0]
    assert count == n_second, "Chunk count should match second ingest, not doubled"
    assert n_first == n_second


def test_chunk_and_store_empty_html(
    store: Path, db: sqlite3.Connection, tmp_path: Path
) -> None:
    """chunk_and_store returns 0 and does not crash when HTML has no text."""
    html_path = tmp_path / "empty.html"
    html_path.write_text("<html><head></head><body></body></html>", encoding="utf-8")
    artifact = _make_artifact_dc(store, str(html_path), slug="empty-slug")
    ingest.save_artifact(db, store, artifact)
    artifact_id = db.execute("SELECT id FROM artifacts WHERE slug = ?", (artifact.slug,)).fetchone()[0]

    n = ingest.chunk_and_store(db, artifact_id, html_path)

    assert n == 0
