# EvoResearch — Project Context

## Orientation

Read these in order before touching the codebase:

1. [VISION.md](./VISION.md) — what we're building and why
2. [ROADMAP.md](./ROADMAP.md) — phases A through I with versions and acceptance criteria
3. [SPEC.md](./SPEC.md) — master system specification
4. [specs/](./specs/) — phase-specific specifications, read the one matching the current phase
5. [CHANGELOG.md](./CHANGELOG.md) — what's actually shipped

## What this is

EvoResearch is a learning and research partner that builds and protects your understanding of any domain. The research counterpart to Hermes. Not RAG over notes — RAG is a feature. The system ingests sources from many places, structures them into compounding understanding, keeps that understanding honest as it grows (reconciliation, fact-checking — quality mechanisms in service of learning), and serves it back through chat, browse, and agent loops.

## Key paths

- **Research store (vault):** `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Samuel's Vault/HomeOS/Knowledge/Research/`
  - `manifest.db` — SQLite with FTS5 (+ sqlite-vec from Phase C)
  - `html/` — permanent HTML research pages
  - `summaries/` — companion .md notes
- **Portal app:** `portal/` (Next.js 16)
- **Scripts:** `scripts/` — `ingest.py` (shipped), `embed.py` (Phase C), `reconcile.py` (Phase E), `agent.py` (Phase F)
- **Migrations:** `scripts/migrations/` — versioned forward-only SQL (from Phase C onwards)

## Current state

**Shipped:** v0.1.0 — Phases A + B complete (ingest pipeline + local portal).

**Active:** **Phase C — Intelligence Layer** (RAG + chat + claim stub). Target release v0.2.0. Detailed spec at [specs/phase-c-rag.md](./specs/phase-c-rag.md).

**Next:** Phase D (multi-source ingest), then E (reconciliation), F (agents), G (portable), H (open source v1.0).

## Commands

```bash
# Phase A (shipped) — ingest
uv run scripts/ingest.py --title "..." --slug "..." --tags "..." --topics "..." --summary "..." --html /path/to/file.html
uv run scripts/ingest.py --search "keyword"
uv run scripts/ingest.py --list

# Phase B (shipped) — portal
cd portal && bun dev

# Phase C (coming in v0.2.0)
uv run scripts/embed.py --rebuild
uv run scripts/embed.py --incremental

# Tests (must pass before every commit)
uv run pytest
cd portal && bun test && bun run build
```

## Stack

- **Brain:** Python 3.12+, `uv`, SQLite FTS5 + sqlite-vec (Phase C), `pytest`
- **Portal:** Next.js 16, React 19, Tailwind v4, shadcn/ui, Biome, `bun`, `better-sqlite3`
- **LLM (Phase C):** Anthropic for chat, OpenAI for embeddings, abstracted via `Provider` interface

## Rules

- Raw SQL only (no ORM)
- `pathlib.Path` for all paths; never string paths
- Never hardcode home dir — use `Path.home()` or `EVO_RESEARCH_STORE`
- Never write research to `/tmp`
- Atomic DB operations always
- FTS triggers and vec sync must be exercised by tests
- All schema changes from Phase C onwards ship as versioned migrations
- Run `uv run pytest && cd portal && bun test && bun run build` before every commit
- Every phase ships a tagged release with a complete CHANGELOG entry

## Working agreement

- **Samuel** — Product Owner. Approves vision changes, phase reordering, public-API changes.
- **Hermes** — Product Manager. Writes per-phase plan (`tasks/plan-phase-X.md`) resolving open questions before implementation begins.
- **Claude Code** — Software Engineer. Implements per the phase spec; raises architectural deviations as questions, not silent changes.

When in doubt about a trade-off, see the decision principle in VISION.md: **does this deepen the user's understanding of their domain over time, or does it just add features?**
