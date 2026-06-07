# EvoResearch — Project Context

## Orientation

Read these in order before touching the codebase:

1. [VISION.md](./VISION.md) — agents do the work, you direct them, the KB is what they build, chat is how you query what they built. The **Engineering positioning** section names the AI Platform Engineering thesis explicitly.
2. [ROADMAP.md](./ROADMAP.md) — phases A through J with versions and acceptance criteria. Each phase Goal leads with the platform capability it delivers.
3. [CAPABILITIES.md](./CAPABILITIES.md) — every platform capability the system embodies, shipped or planned, tied to the phase that delivered it and the user pressure that justified it.
4. [SPEC.md](./SPEC.md) — master system specification
5. [specs/](./specs/) — phase-specific specifications, read the one matching the current phase
6. [CHANGELOG.md](./CHANGELOG.md) — what's actually shipped

## What this is

EvoResearch is an **agent-first learning platform**. You direct agents to go deep on a topic. They research it, write structured notes into the KB, then teach you from those notes. Every session compounds into the next. Chat is the retrieval surface for querying what agents built.

**Not a chatbot.** Not a RAG app with agents planned later. A platform where agents are primary, chat is secondary, and the KB compounds with every run.

**Engineering positioning:** EvoResearch is built as an agent platform product, not a RAG app. The primary interface is agent invocation. The primary output is a compounding knowledge base. The secondary interface is retrieval over what agents built. Every phase adds capability that earns its place because the product demanded it. See [CAPABILITIES.md](./CAPABILITIES.md) for the full map.

## Key paths

- **Research store (vault):** `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Samuel's Vault/HomeOS/Knowledge/Research/`
  - `manifest.db` — SQLite with FTS5 + sqlite-vec
  - `html/` — permanent HTML research pages
  - `summaries/` — companion .md notes
- **Core:** `core/` — platform harness primitives
  - `core/llm/` — Provider protocol + BedrockProvider
  - `core/memory/` — db helpers, retrieval, chunker
  - `core/runtime/` — agent execution loop (Phase D)
  - `core/tools/` — tool interface (Phase D)
  - `core/prompts/` — skill instruction sets (Phase D)
  - `core/governance/` — audit + allowlist (Phase D)
- **Server:** `server.py` — FastAPI (`/chat`, `/agent` in Phase D)
- **Portal:** `portal/` (Next.js 16)
- **Scripts:** `scripts/` — `ingest.py`, `embed.py`, agent scripts (Phase D)
- **Migrations:** `scripts/migrations/` — versioned forward-only SQL

## Current state

**Shipped:**
- v0.1.0 — Phases A + B (ingest pipeline + local portal)
- **v0.2.0 — Phase C: Intelligence Substrate** — provider abstraction (Bedrock-only: Claude Sonnet 4.6 + Cohere Embed v4), hybrid retrieval (vec + FTS + score-based merge), embedding pipeline, eval harness (gate 8/10, currently 10/10), chat surface, migration 002 (chunks + embeddings + claims stub), 84 tests passing + 2 skipped

**Active:**
- **Phase D — Agent Foundation** — target release v0.3.0
- Detailed spec at [specs/phase-d-agent-foundation.md](./specs/phase-d-agent-foundation.md)
- Patch in flight: v0.2.0.1 — markdown rendering fix in chat surface, vitest pre-existing failures

**Next after Phase D:**
- E — Multi-source Ingest (v0.4.0)
- F — Knowledge Quality / claims activation (v0.5.0)
- G — Agent Expansion + async runtime + web_search (v0.6.0)
- H — Portable / OSS-ready (v0.7.0)
- I — Open Source Release (v1.0.0)
- J — Hosted Option (v2.0.0, conditional)

## Commands

```bash
# Phase A (shipped) — ingest
uv run scripts/ingest.py --title "..." --slug "..." --tags "..." --topics "..." --summary "..." --html /path/to/file.html
uv run scripts/ingest.py --search "keyword"
uv run scripts/ingest.py --list

# Phase B (shipped) — portal
cd portal && bun dev

# Phase C (shipped, v0.2.0) — embeddings + chat
uv run scripts/embed.py --rebuild
uv run scripts/embed.py --incremental
uvicorn server:app --port 8765  # FastAPI server (file at repo root)

# Phase D (coming in v0.3.0) — agent runtime
uv run scripts/agent.py --task research --topic "..." --mode concept
uv run scripts/agent.py --task teach --topic "..."

# Tests (must pass before every commit)
uv run pytest
cd portal && bun test && bun run build
```

## Stack

- **Languages:** Python 3.12+, TypeScript
- **Brain:** Python + uv + FastAPI + SQLite (FTS5 + sqlite-vec) + pytest
- **Portal:** Next.js 16, React 19, Tailwind v4, shadcn/ui, Biome, bun, better-sqlite3
- **LLM (Phase C shipped):** Bedrock-only — Claude Sonnet 4.6 for chat, Cohere Embed v4 for embeddings (1024 dims). Provider abstraction in `core/llm/bedrock.py`, swappable via `EVO_LLM_PROVIDER` (currently only `bedrock` implemented).
- **Auth:** `~/.zshrc` exports `AWS_PROFILE=my-bedrock-profile` and `AWS_REGION=us-east-1` globally

## Rules

- Raw SQL only (no ORM)
- `pathlib.Path` for all paths; never string paths
- Never hardcode home dir — use `Path.home()` or `EVO_RESEARCH_STORE`
- Never write research to `/tmp`
- Atomic DB operations always
- FTS triggers and vec sync must be exercised by tests
- All schema changes from Phase C onwards ship as versioned migrations
- Phase D wraps Phase C code in Tool interfaces. **No retrieval rebuild. No Provider rewrite.** Reuse, don't rewrite.
- Eval harness from Phase C must still pass 10/10 after every Phase D merge
- Every agent run records `cost_tokens` and `cost_usd` from run zero. Cost caps land in Phase G.
- Run `uv run pytest && cd portal && bun test && bun run build` before every commit
- Every phase ships a tagged release with a complete CHANGELOG entry

## Structure decisions (locked)

- `agents/` goes inside `core/agents/` when Phase D creates it — not top-level
- `server.py` → `server/` with `routes/`, `middleware/`, `config.py`, `utils/` when `/agent` route lands in Phase D — that's the threshold
- No phantom files — only create files in the phase that needs them

## Working agreement

- **Samuel** — Product Owner. Approves vision changes, phase reordering, public-API changes.
- **Hermes** — Product Manager. Writes per-phase plan (`tasks/plan-phase-X.md`) resolving open questions before implementation begins.
- **Claude Code** — Software Engineer. Implements per the phase spec; raises architectural deviations as questions, not silent changes.

## Decision principle

When a feature decision is unclear:

> **Does this make the agent loop richer, or does it just add features?**

Richer agent loop wins. Features don't.
