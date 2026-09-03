# EvoMind — Project Context

## What this is

EvoMind is a personal knowledge base with hybrid RAG retrieval — vector + full-text search fused into one pipeline, with cited answers over your research corpus. Built with Python (FastAPI + SQLite) on the backend and Next.js 16 on the frontend.

**Engineering thesis:** Storage at the foundation. Retrieval fused from multiple signals. A thin LLM layer on top for cited Q&A.

## Key paths

- **Research store (vault):** Configurable via `EVO_STORE` env var
  - `manifest.db` — SQLite with FTS5 + sqlite-vec
  - `html/` — permanent HTML research pages
  - `summaries/` — companion .md notes
- **Core:** `core/` — retrieval, embedding, and LLM primitives
  - `core/llm/` — Provider protocol + OpenRouter / Bedrock backends
  - `core/memory/` — db helpers, hybrid retrieval, chunker
  - `core/runtime/` — agent execution loop (research + teach tasks)
  - `core/tools/` — tool interface (retrieve, generate, ingest)
  - `core/prompts/` — instruction templates
  - `core/governance/` — audit + allowlist
- **Server:** `server/` — FastAPI package (`/chat` for Q&A, `/api/agent` for tasks)
- **Portal:** `portal/` — Next.js 16 (Landing, Wiki, Wiki Detail, Search, Docs)
- **Scripts:** `scripts/` — `ingest.py`, `embed.py`, `eval.py`, `agent.py`, `migrate.py`
- **Migrations:** `scripts/migrations/` — versioned forward-only SQL

## Commands

```bash
# Seed sample data (if needed)
uv run scripts/ingest.py --html /path/to/file.html --title "..." --slug "..." --tags "..." --topics "..." --summary "..."

# Embed chunks
uv run scripts/embed.py --incremental

# Start server
uvicorn server:app --port 8765

# Portal
cd portal && bun dev

# Tests (must pass before every commit)
uv run pytest
cd portal && bun test && bun run build
```

## Stack

- **Backend:** Python 3.12+ · FastAPI · SQLite (FTS5 + sqlite-vec) · OpenRouter (Gemma 4) · fastembed · pytest (150+ tests)
- **Frontend:** Next.js 16 · React 19 · Tailwind v4 · shadcn/ui · better-sqlite3 · Biome · bun
- **Auth:** `OPENROUTER_API_KEY` env var for LLM chat

## Rules

- Raw SQL only (no ORM)
- `pathlib.Path` for all paths; never string paths
- Never hardcode home dir — use `Path.home()` or `EVO_STORE`
- Atomic DB operations always
- All schema changes ship as versioned migrations
- Eval harness must pass 10/10 after every merge
- Run `uv run pytest && cd portal && bun test && bun run build` before every commit
