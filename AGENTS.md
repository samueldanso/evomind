# NeuroWiKi — Project Context

## What this is

NeuroWiKi is an AI-powered personal knowledge base — a portfolio project demonstrating hybrid RAG retrieval, autonomous research agents, and a compounding knowledge graph. Built with Python (FastAPI + SQLite) on the backend and Next.js 16 on the frontend.

**Engineering thesis:** Agent runtime first. Tools that agents call second. Retrieval as a tool third. Storage at the foundation.

## Key paths

- **Research store (vault):** Configurable via `EVO_STORE` env var
  - `manifest.db` — SQLite with FTS5 + sqlite-vec
  - `html/` — permanent HTML research pages
  - `summaries/` — companion .md notes
- **Core:** `core/` — platform harness primitives
  - `core/llm/` — Provider protocol + BedrockProvider
  - `core/memory/` — db helpers, retrieval, chunker
  - `core/runtime/` — agent execution loop
  - `core/tools/` — tool interface (retrieve, generate, ingest)
  - `core/prompts/` — agent instruction templates
  - `core/governance/` — audit + allowlist
- **Server:** `server/` — FastAPI package (`/chat`, `/api/agent`)
- **Portal:** `portal/` — Next.js 16 (Landing, Wiki, Wiki Detail, Search)
- **Scripts:** `scripts/` — `ingest.py`, `embed.py`, `eval.py`, `agent.py`, `migrate.py`
- **Migrations:** `scripts/migrations/` — versioned forward-only SQL

## Commands

```bash
# Ingest research
uv run scripts/ingest.py --title "..." --slug "..." --tags "..." --topics "..." --summary "..." --html /path/to/file.html

# Embed + serve
uv run scripts/embed.py --incremental
uvicorn server:app --port 8765

# Portal
cd portal && bun dev

# Research agent
uv run scripts/agent.py --task research --topic "..." --mode concept

# Tests (must pass before every commit)
uv run pytest
cd portal && bun test && bun run build
```

## Stack

- **Backend:** Python 3.12+ · FastAPI · SQLite (FTS5 + sqlite-vec) · AWS Bedrock (Claude Sonnet 4.6 + Cohere Embed v4) · pytest (153 tests)
- **Frontend:** Next.js 16 · React 19 · Tailwind v4 · shadcn/ui · better-sqlite3 · Biome · bun
- **Auth:** `AWS_PROFILE` + `AWS_REGION` env vars for Bedrock access

## Rules

- Raw SQL only (no ORM)
- `pathlib.Path` for all paths; never string paths
- Never hardcode home dir — use `Path.home()` or `EVO_STORE`
- Atomic DB operations always
- All schema changes ship as versioned migrations
- Eval harness must pass 10/10 after every merge
- Run `uv run pytest && cd portal && bun test && bun run build` before every commit
