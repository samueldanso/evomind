# EvoResearch Phase A — Task Checklist

## Phase 1: Project Foundation

- [ ] **T1** — Initialize uv project (`pyproject.toml`, `scripts/`, `tests/`)
- [ ] **T2** — `get_store_path()` + `bootstrap_store()` with env var override + tests
- [ ] **T3** — `init_db()`: schema + FTS5 virtual table + 3 triggers + tests

### Checkpoint A
- [ ] `uv run pytest` passes
- [ ] DB schema + triggers confirmed

---

## Phase 2: Core CLI

- [ ] **T4** — `save_artifact()` + `write_companion_md()` + HTML copy + upsert + tests
- [ ] **T5** — `search_artifacts()` FTS5 BM25 + `--search` CLI + tests
- [ ] **T6** — `list_artifacts()` + `--list` CLI + tests

### Checkpoint B
- [ ] `uv run pytest` passes
- [ ] End-to-end ingest → search → list works

---

## Phase 3: 100% Coverage

- [ ] **T7** — Complete pytest suite: error paths, FTS trigger sync, 100% coverage
  - `uv run pytest --cov=scripts/ingest` → 100%

### Checkpoint C
- [ ] 100% coverage confirmed

---

## Phase 4: Portal Scaffold

- [ ] **T8** — `portal/` scaffold: Next.js 15 + Tailwind v4 + Biome + `bun run build` passes

---

## Phase 5: Git

- [ ] **T9** — `.gitignore` + `git init` + first commit (tests pass pre-commit)

### Final Checkpoint
- [ ] `uv run pytest --cov=scripts/ingest` → all pass, 100%
- [ ] `cd portal && bun run build` → exits 0
- [ ] `git log --oneline` → 1 clean commit
