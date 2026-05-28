# EvoResearch — Project Context

## What This Is

A persistent, corpus-aware research knowledge system for Samuel Danso.
See SPEC.md for the full specification.

## Key Paths

- **Research store (vault):** `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Samuel's Vault/HomeOS/Knowledge/Research/`
  - `manifest.db` — SQLite with FTS5, all artifact metadata
  - `html/` — permanent HTML research pages
  - `summaries/` — companion .md notes
- **Portal app:** `portal/` (Next.js 16, Phase B)
- **Scripts:** `scripts/ingest.py` — CLI for saving artifacts + querying manifest

## Commands

```bash
# Ingest a research artifact
uv run scripts/ingest.py --title "..." --slug "..." --tags "..." --topics "..." --summary "..." --html /path/to/file.html

# Search
uv run scripts/ingest.py --search "keyword"

# List all
uv run scripts/ingest.py --list

# Run tests
uv run pytest

# Portal dev (Phase B)
cd portal && bun dev
```

## Stack

- Python 3.12+, `uv`, SQLite FTS5, `pytest`
- Portal: Next.js 16, Tailwind v4, shadcn/ui (card, input, badge), Biome, `bun`

## Rules

- Raw SQL only (no ORM)
- `pathlib.Path` for all paths
- Never hardcode home dir — use `Path.home()` or `EVO_RESEARCH_STORE` env var
- Never write research to `/tmp`
- Atomic DB operations always
- FTS triggers must be set up — search is core
- Run `uv run pytest` before every commit

## Current Phase

**Phase B — Checkpoint A complete** (Tasks 1 + 2 done, reviewed, CI gates on pytest + bun build)
- T1 ✅ — db layer (`lib/db.ts`, `lib/types.ts`), better-sqlite3, shadcn foundation
- T2 ✅ — `GET /api/artifacts`, `ArtifactCard`, `ArtifactGrid`, `page.tsx` wired
- T3 next — tag filter (client state, OR logic)
- T4 — FTS5 search
- T5 — artifact viewer + iframe

Phase A is complete: `scripts/ingest.py` fully implemented, 37/37 tests passing, `manifest.db` schema live at vault path.
