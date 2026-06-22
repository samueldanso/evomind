# Changelog

All notable changes to Evo are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

---

## [0.3.1] - 2026-06-08

### Fixed

- Research artifacts now render with white background in KB viewer (light CSS override injected at ingest time)
- `scripts/fix_summaries.py` — one-time retrofix strips raw HTML/markdown fences from existing artifact summaries

### Added — Phase D.1: Interactive Teaching Session

- `scripts/migrations/004_phase_d1.sql` — `session_log` TEXT column on `agent_runs`
- `core/governance/audit.py` — `pause_run()`, `resume_run()`, `get_run()` now returns `session_log`
- `core/runtime/contracts.py` — `paused_awaiting_input` status, `session_log` field on `AgentRun`
- `core/agents/teaching.py` — `run_teaching_turn()` with per-turn pause/resume logic
- `server/routes/agent.py` — real `POST /{run_id}/message` handler replaces stub; teaching dispatch starts interactive session
- `portal/components/teach-session.tsx` — conversation thread UI with 2s polling, input box, typing indicator
- `portal/components/run-status.tsx` — wires `TeachSession` when teaching run is `paused_awaiting_input`

### Tests

- 153 Python tests passing (+16 new: CSS inject, summary strip, audit pause/resume, teaching turn), 2 skipped behind `RUN_LIVE_LLM=1`
- Portal: 48 tests passing (+7 new: message proxy route, teach session API interactions)

---

## [0.3.0] - 2026-06-08

### Fixed — Post-release patches (live E2E T8)

- `f09b3a2` fix(portal): force light background on artifact iframe to prevent black render
- `fb16b3b` fix(agents): strip HTML tags from research summary before storing
- `aefef6a` fix(portal): pre-fill topic from slug when navigating via "Teach me this"
- `34c264a` feat(tools): embed new chunks inline after ingest for immediate retrieval

### Notes

Teaching Agent ships as non-interactive (auto-advance 3 turns) in this release. Interactive session UI (`teach-session.tsx`, real `/message` polling loop, `paused_awaiting_input` state machine) is deferred to v0.3.1.

---

### Added — Phase D: Agent Foundation

- `scripts/migrations/003_phase_d.sql` — `agent_runs` table with indexes for status and agent_type queries
- `core/runtime/contracts.py` — typed task contracts (`ResearchTask`, `TeachTask`, `ToolCallRecord`, `AgentRun`) with `validate_task()` dispatch-time validation
- `core/runtime/loop.py` — `run_agent()` execution loop with tool-call closure, allowlist enforcement, and audit recording
- `core/runtime/dispatcher.py` — `dispatch()` with auto-chain (Research → Teaching by default)
- `core/governance/allowlist.py` — per-agent tool allowlists with `PermissionError` on violation
- `core/governance/audit.py` — `create_run`, `record_tool_call`, `complete_run`, `fail_run`, `get_run`, `list_runs` — full agent_runs lifecycle
- `core/tools/base.py` — `Tool` dataclass and `ToolRegistry` container
- `core/tools/retrieve.py` — wraps `hybrid_search` as a tool closure
- `core/tools/generate.py` — wraps `provider.chat()` as a tool closure
- `core/tools/ingest.py` — wraps artifact save + chunk_and_store as a tool closure
- `core/tools/web_search.py` — stub returning empty results (real implementation Phase G)
- `core/agents/research.py` — research agent: retrieve → generate notes → produce HTML → ingest (4 tool calls)
- `core/agents/teaching.py` — teaching agent: retrieve → opening → multi-turn → connections → checklist → ingest
- `core/prompts/templates.py` — system prompts and instruction templates for research and teaching agents
- `scripts/agent.py` — CLI entry point: `--task research|teach --topic "..." --mode concept|tool|company`
- `server/` — FastAPI restructured from single file to package with `routes/chat.py` and `routes/agent.py`
- `server/routes/agent.py` — `POST /api/agent`, `GET /api/agent/runs`, `GET /api/agent/{run_id}`, `POST /api/agent/{run_id}/message`
- Portal: agent invocation form as home page (`/`), artifact grid moved to `/kb`, run history at `/runs`
- `portal/components/agent-form.tsx` — task type, mode, slug, context, auto-teach toggle
- `portal/components/run-status.tsx` — run result display with status badges and artifact links
- `portal/components/run-history.tsx` — recent runs list with type/status/topic/cost
- `portal/lib/agent-client.ts` — typed API client for agent dispatch, run fetch, message send, run listing

### New commands

```bash
uv run scripts/agent.py --task research --topic "..." --mode concept
uv run scripts/agent.py --task teach --topic "..."
```

### Tests

- 137 Python tests passing, 2 skipped behind `RUN_LIVE_LLM=1`
- Portal: 41 vitest tests pass (agent client, proxy routes, chat client, search/artifact routes)

---

## [0.2.0] - 2026-05-29

### Added — Phase C: Intelligence Layer

- `scripts/migrations/002_phase_c.sql` — `chunks`, `embeddings` (sqlite-vec `vec0`), `claims` stub, `claim_sources`, and `migrations` tracking tables
- `scripts/migrate.py` — forward-only migration runner with backup enforcement and sqlite-vec loading
- `core/memory/chunker.py` — sentence-boundary-respecting text splitter (`chunk_size=800`, `overlap=100`); trafilatura extraction with BS4 fallback
- `scripts/ingest.py` patched — `chunk_and_store()` runs automatically on every artifact ingest; re-ingest is idempotent
- `core/llm/bedrock.py` — `Provider` protocol with `BedrockProvider` (boto3); Claude Sonnet 4.6 for chat, Cohere Embed v4 at 1024 dims for embeddings; `get_provider()` factory; provider swappable via `EVO_LLM_PROVIDER` env var (default `bedrock`)
- `scripts/embed.py` — incremental (default) and rebuild embed pipeline; batch size 64; exponential backoff on rate limits; progress output
- `core/memory/retrieval.py` — `fts_search` (BM25 over FTS5), `vec_search` (sqlite-vec cosine), `hybrid_search` (sequential merge, dedup by chunk_id, `match_type` tagging)
- `server.py` — FastAPI server on `EVO_CHAT_PORT` (default 8765); `POST /chat` embeds query → hybrid retrieval → Bedrock generation → answer + sources; `GET /health` reports corpus stats; DB opened once at startup via lifespan
- `portal/lib/chat.ts` — typed chat client (`ChatRequest`, `ChatSource`, `ChatResponse`); throws on non-200 with error passthrough
- `portal/app/chat/page.tsx` — chat UI: query input, answer prose, source list with `match_type` badges and scores; dark/light theme aware
- `scripts/eval.py` — 10-question retrieval smoke test; exits 0 if ≥8/10 questions return at least one result; retrieval-only (no generation cost)

### New commands

```bash
uv run scripts/migrate.py              # apply pending migrations
uv run scripts/embed.py --incremental  # embed new chunks only (default)
uv run scripts/embed.py --rebuild      # re-embed all chunks
uv run scripts/eval.py                 # run retrieval smoke test
uvicorn server:app --port 8765         # start chat server
```

### New environment variables

| Variable | Default | Purpose |
|---|---|---|
| `AWS_PROFILE` | — | AWS credentials profile for Bedrock access |
| `AWS_REGION` | `us-east-1` | AWS region for Bedrock API calls |
| `EVO_LLM_PROVIDER` | `bedrock` | Select LLM provider (currently only `bedrock`) |
| `EVO_CHAT_PORT` | `8765` | FastAPI server port |

### Tests

- 84 Python tests passing, 2 skipped behind `RUN_LIVE_LLM=1`
- Portal: 4 vitest tests pass (Phase C chat client); 4 pre-existing Phase B tests have `vi.hoisted` compatibility errors — fix in flight as v0.2.0.1 patch

### Post-release notes

Post-release commits `59989c0` and `87a8fe2` replaced the original Anthropic + OpenAI provider implementation with Bedrock-only (boto3). This changelog reflects what's actually in the codebase after those commits landed on main.

---

## [0.1.0] - 2026-05-28

### Added — Phase A: Ingest pipeline

- `scripts/ingest.py` — CLI to ingest HTML research artifacts into a SQLite FTS5 manifest
- SQLite schema: `artifacts` table + `artifacts_fts` virtual table with insert/update/delete triggers
- Vault layout: `html/` for permanent HTML pages, `summaries/` for companion `.md` notes
- `EVO_STORE` env var for vault path override (used by tests and CI)
- `--html`, `--search`, `--list` CLI modes
- 37 pytest tests with 100% coverage of `ingest.py`

### Added — Phase B: Local research portal

- Next.js 16 portal (`portal/`) — Tailwind v4, shadcn/ui, Biome, bun
- Card grid home page — artifacts ordered by date, responsive 1/2/3-column layout
- Tag filter — client-side OR logic, badge toggles, no API round-trip
- Full-text search — debounced 300ms → `GET /api/search?q=` → FTS5 BM25 ranking
- Artifact detail viewer — iframe renders original HTML with its own styling preserved
- Path confinement guard — all `html_path` access confined to vault root
- Security headers — `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`
- FTS5 injection protection — token quoting + double-quote stripping in `ftsEscape()`
- 33 vitest tests covering all four API route handlers
- CI: GitHub Actions gates on `pytest`, `bun run test`, and `bun run build`

[Unreleased]: https://github.com/samueldanso/evo/compare/v0.3.1...HEAD
[0.3.1]: https://github.com/samueldanso/evo/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/samueldanso/evo/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/samueldanso/evo/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/samueldanso/evo/releases/tag/v0.1.0
