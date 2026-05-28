# Implementation Plan: EvoResearch Phase A

## Overview

Build the persistent research knowledge system brain: a SQLite manifest with FTS5, a Python CLI (`ingest.py`) for saving and querying artifacts, and a scaffolded Next.js portal ready for Phase B. All research data lives at the iCloud vault path; all tooling lives in this git repo.

## Architecture Decisions

- **Store path resolution:** `EVO_RESEARCH_STORE` env var → `Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/Samuel's Vault/HomeOS/Knowledge/Research"` fallback. Never hardcoded.
- **Single DB file:** `manifest.db` at store root. FTS5 via content table + 3 triggers (insert/update/delete). stdlib `sqlite3` only — no external deps.
- **CLI mode dispatch:** `argparse` with mutually exclusive group: `--html` triggers ingest, `--search` triggers FTS query, `--list` dumps JSON. Positional args invalid.
- **Dataclass + `asdict`:** `Artifact` dataclass for type safety; raw SQL via `sqlite3.Connection`.
- **Companion `.md`:** Every ingest writes `summaries/{slug}.md` with YAML frontmatter for Obsidian.
- **Tests:** `pytest` with a `tmp_path` fixture DB — never touches the real vault during tests. 100% coverage of all functions in `ingest.py`.
- **Portal scaffold:** `bun create next-app portal` with Next.js 15, App Router, Tailwind v4, TypeScript, Biome. No portal implementation in Phase A.

## Dependency Graph

```
Task 1: uv project init (pyproject.toml)
    │
    └── Task 2: Vault path + DB init (store.py helpers embedded in ingest.py)
            │
            ├── Task 3: Schema + FTS triggers
            │       │
            │       └── Task 4: ingest.py CLI (save + search + list)
            │               │
            │               └── Task 5: pytest suite (100% coverage)
            │
            └── Task 6: Portal scaffold (independent after Task 1)

Task 7: git init + first commit (depends on all above)
```

---

## Phase 1: Project Foundation

### Task 1: Initialize uv project

**Description:** Create `pyproject.toml` with Python 3.12+, `pytest` as dev dependency, and project metadata. Establish the `scripts/` and `tests/` directories.

**Acceptance criteria:**
- [ ] `pyproject.toml` exists with `[project]` name `evo-research`, requires-python `>=3.12`
- [ ] `pytest` listed under `[dependency-groups] dev`
- [ ] `uv run pytest` resolves without import errors (no tests yet → exits 0 with "no tests found")
- [ ] `scripts/` and `tests/` directories exist (with `__init__.py` in `tests/`)

**Verification:**
- [ ] `uv run python --version` prints 3.12+
- [ ] `uv run pytest --collect-only` exits 0

**Dependencies:** None

**Files touched:**
- `pyproject.toml`
- `scripts/.gitkeep` (or first script)
- `tests/__init__.py`

**Estimated scope:** Small

---

### Task 2: Vault store path resolution + directory bootstrap

**Description:** Implement `get_store_path()` and `bootstrap_store()` functions (inside `ingest.py`) that resolve the vault path, create `html/` and `summaries/` subdirs if absent, and return the root `Path`.

**Acceptance criteria:**
- [ ] `EVO_RESEARCH_STORE` env var overrides default when set
- [ ] Default path resolves to `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Samuel's Vault/HomeOS/Knowledge/Research`
- [ ] `html/` and `summaries/` dirs are created if missing
- [ ] Function is pure — no side effects beyond directory creation

**Verification:**
- [ ] Unit test with `tmp_path` confirms both subdirs created
- [ ] Unit test with custom env var confirms override

**Dependencies:** Task 1

**Files touched:**
- `scripts/ingest.py`
- `tests/test_ingest.py`

**Estimated scope:** Small

---

### Task 3: SQLite schema + FTS5 triggers

**Description:** Implement `init_db(db_path: Path) -> sqlite3.Connection` that creates `artifacts`, `artifacts_fts`, and all three triggers (AI/AU/AD) in a single atomic transaction. Idempotent — safe to call if schema already exists.

**Acceptance criteria:**
- [ ] `artifacts` table matches spec schema exactly (all 10 columns)
- [ ] `artifacts_fts` virtual table with `content='artifacts'` and `content_rowid='id'`
- [ ] All three triggers exist: `artifacts_ai`, `artifacts_au`, `artifacts_ad`
- [ ] Calling `init_db` twice on same DB does not raise (uses `CREATE TABLE IF NOT EXISTS`)
- [ ] Returns open `sqlite3.Connection` with `row_factory = sqlite3.Row`

**Verification:**
- [ ] Test: `SELECT name FROM sqlite_master WHERE type='table'` returns `artifacts` and `artifacts_fts`
- [ ] Test: `SELECT name FROM sqlite_master WHERE type='trigger'` returns all 3 trigger names

**Dependencies:** Task 2

**Files touched:**
- `scripts/ingest.py`
- `tests/test_ingest.py`

**Estimated scope:** Small

---

### Checkpoint A — Foundation

- [ ] `uv run pytest tests/` passes
- [ ] DB initializes cleanly at a tmp path
- [ ] Schema and triggers confirmed via sqlite_master queries

---

## Phase 2: Core CLI — Ingest + Search + List

### Task 4: `ingest` command — save artifact + copy HTML + write companion .md

**Description:** Implement `save_artifact(db, store, artifact)` and `write_companion_md(store, artifact)`. The CLI `--html` path triggers: copy HTML to `html/{slug}-{YYYY-MM-DD}.html`, write `summaries/{slug}.md` with YAML frontmatter, upsert DB row. All in one atomic sequence.

**Acceptance criteria:**
- [ ] HTML file is copied (not moved) to `store/html/{slug}-{date}.html`
- [ ] `summaries/{slug}.md` is written with frontmatter: title, slug, tags (list), topics (list), summary, created_at, html_path
- [ ] DB row is inserted; re-running same slug updates title/summary/tags/topics and `updated_at`, does not duplicate
- [ ] `html_path` stored in DB is the absolute destination path (not the source)
- [ ] `md_path` stored in DB is the absolute `.md` path
- [ ] Exit code 0 on success; prints confirmation to stdout

**Verification:**
- [ ] Test: save artifact → files exist at expected paths
- [ ] Test: save same slug twice → single DB row, `updated_at` changed
- [ ] Test: FTS insert trigger fires → artifact queryable by title keyword immediately after insert

**Dependencies:** Task 3

**Files touched:**
- `scripts/ingest.py`
- `tests/test_ingest.py`

**Estimated scope:** Medium

---

### Task 5: `search` command — FTS5 query with ranked output

**Description:** Implement `search_artifacts(db, query) -> list[dict]`. Uses `artifacts_fts` with `bm25` ranking. CLI `--search` prints JSON array of matching artifacts (all fields), ordered by relevance. Returns empty array (not error) for no matches.

**Acceptance criteria:**
- [ ] Returns results ranked by BM25 relevance
- [ ] Searches across slug, title, summary, tags, topics
- [ ] Empty query string raises `argparse` error (not crash)
- [ ] No matches → prints `[]` and exits 0
- [ ] Results include all artifact fields as JSON
- [ ] P99 latency < 100ms on corpus of 1000 artifacts (tested with timing)

**Verification:**
- [ ] Test: insert artifact with known title → `--search` on title keyword returns it
- [ ] Test: delete artifact → no longer returned in search
- [ ] Test: update artifact → updated fields searchable

**Dependencies:** Task 4

**Files touched:**
- `scripts/ingest.py`
- `tests/test_ingest.py`

**Estimated scope:** Small

---

### Task 6: `list` command — dump all artifacts as JSON

**Description:** Implement `list_artifacts(db) -> list[dict]`. CLI `--list` prints full JSON array of all artifacts ordered by `created_at DESC`. Empty DB → `[]`.

**Acceptance criteria:**
- [ ] Returns all rows, all fields, as JSON array
- [ ] Ordered newest-first
- [ ] Empty DB returns `[]` and exits 0
- [ ] JSON is pretty-printed (indent=2)

**Verification:**
- [ ] Test: insert 3 artifacts → `--list` returns all 3 in correct order
- [ ] Test: empty DB → `[]`

**Dependencies:** Task 4

**Files touched:**
- `scripts/ingest.py`
- `tests/test_ingest.py`

**Estimated scope:** Small

---

### Checkpoint B — Core CLI

- [ ] `uv run pytest` passes, all functions covered
- [ ] `uv run scripts/ingest.py --title "Test" --slug "test" --tags "a" --topics "b" --summary "s" --html /path/to/file.html` works end-to-end
- [ ] `uv run scripts/ingest.py --search "test"` returns result
- [ ] `uv run scripts/ingest.py --list` returns JSON array

---

## Phase 3: Tests to 100% Coverage

### Task 7: Complete pytest suite — 100% coverage on ingest.py

**Description:** Write all remaining tests to reach 100% coverage. Cover error paths: missing HTML source file, invalid slug (spaces), DB connection failure (via monkeypatch), missing required args. Verify FTS sync on all three trigger paths (insert, update, delete).

**Acceptance criteria:**
- [ ] `uv run pytest --cov=scripts/ingest --cov-report=term-missing` shows 100%
- [ ] Test: source HTML path does not exist → exits non-zero with stderr message
- [ ] Test: FTS delete trigger — delete artifact → not returned by search
- [ ] Test: FTS update trigger — update artifact title → new title searchable
- [ ] Test: `--list` with multiple artifacts → correct JSON order
- [ ] All tests use `tmp_path` — zero touching real vault

**Verification:**
- [ ] `uv run pytest --cov=scripts/ingest` exits 0 with 100% coverage

**Dependencies:** Tasks 4, 5, 6

**Files touched:**
- `tests/test_ingest.py`
- `pyproject.toml` (add pytest-cov to dev deps)

**Estimated scope:** Medium

---

## Phase 4: Portal Scaffold

### Task 8: Scaffold portal/ with Next.js 15 + Tailwind v4 + Biome

**Description:** Run `bun create next-app` inside `portal/` with App Router, TypeScript, Tailwind CSS, no ESLint (Biome replaces it). Add Biome config. Verify `bun dev` starts without errors. No portal implementation — scaffold only.

**Acceptance criteria:**
- [ ] `portal/package.json` exists with Next.js 15, React 19, Tailwind v4
- [ ] `portal/biome.json` exists with formatter + linter config
- [ ] `bun run dev` in `portal/` starts on port 3000 without errors
- [ ] `bun run build` in `portal/` produces successful build
- [ ] No ESLint config — Biome only
- [ ] `.gitignore` in portal excludes `node_modules/`, `.next/`

**Verification:**
- [ ] `cd portal && bun run build` exits 0
- [ ] `portal/biome.json` exists

**Dependencies:** Task 1 (uv project established)

**Files touched:**
- `portal/` (full Next.js scaffold)
- `portal/biome.json`

**Estimated scope:** Medium

---

### Checkpoint C — Phase A Complete

- [ ] `uv run pytest --cov=scripts/ingest` → 100% coverage, all pass
- [ ] `manifest.db` exists at vault path after one real ingest run
- [ ] `cd portal && bun run build` exits 0
- [ ] Git repo initialized with clean first commit

---

## Phase 5: Git Init + First Commit

### Task 9: Initialize git repo and commit

**Description:** Init git repo, write `.gitignore` (Python, Node, OS artifacts), verify tests pass, commit all Phase A files.

**Acceptance criteria:**
- [ ] `.gitignore` covers: `__pycache__/`, `*.pyc`, `.venv/`, `node_modules/`, `.next/`, `*.db`, `.DS_Store`, `.env`
- [ ] `manifest.db` is gitignored (lives in vault, not repo)
- [ ] `uv run pytest` passes before commit
- [ ] Single commit: "feat: Phase A — persistent store, ingest CLI, portal scaffold"

**Verification:**
- [ ] `git log --oneline` shows 1 commit
- [ ] `git status` clean after commit

**Dependencies:** All prior tasks

**Files touched:**
- `.gitignore`

**Estimated scope:** Small

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Vault path has spaces (iCloud path) | High | Always use `pathlib.Path`, never string concat with paths |
| FTS trigger divergence after schema change | High | Tests verify trigger sync on all 3 operations |
| Portal scaffold version drift | Med | Pin Next.js 15 + React 19 explicitly in create command |
| `uv run` env not finding pytest-cov | Low | Add to `[dependency-groups] dev` in pyproject.toml |

## Open Questions

- None per SPEC.md. Proceed.
