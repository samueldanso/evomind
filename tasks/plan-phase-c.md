# Phase C — Implementation Plan (v0.2.0)

> Hermes (PM) owns this doc. Claude Code reads it before writing a line.
> Spec: [specs/phase-c-rag.md](../specs/phase-c-rag.md)
> Samuel signs off on this plan before implementation starts.

---

## Open questions — resolved

**1. Embedding provider**
→ **OpenAI `text-embedding-3-small`** (1536 dims, ~$0.02/1M tokens).
Voyage is higher quality but requires a separate API key and is overkill for a 7-artifact corpus. Revisit at Phase D when corpus grows. `EVO_EMBED_MODEL` is env-configurable from day one so swapping is a one-liner.

**2. HTML extraction library**
→ **`trafilatura`** as primary, `BeautifulSoup get_text(separator=" ")` as fallback.
`trafilatura` strips nav/footer/ads and preserves sentence flow — better chunk quality than raw BS4. If `trafilatura` returns empty string, fall back to BS4. Both are pure Python, no binary deps.

**3. Streaming chat response**
→ **Synchronous in v0.2.0, streaming in v0.2.1 patch.**
Keeps `POST /api/chat` shape simple for the initial eval. Add `stream: true` parameter in a follow-up patch once the base is stable. Not in acceptance criteria for v0.2.0.

**4. Chat history persistence**
→ **Browser state (React useState) for v0.2.0.**
No DB writes from the portal. Keeps portal read-only (existing architecture constraint). When multi-device or history search matters (Phase G+), add a `conversations` table then.

**5. Source attribution in chat**
→ **Both: artifact title + ±150 chars around the citation hit.**
Title alone is not enough to judge relevance without opening the artifact. The excerpt gives immediate context. `excerpt` field is already in the `Citation` dataclass in the spec.

**6. Chunking strategy** (spec flagged for Hermes to decide)
→ **Fixed-size: 800 chars, 100 char overlap, sentence-boundary-respecting.**
Semantic chunking by headings adds complexity and our HTML sources vary too much in structure. Conservative fixed-size ships faster and is easy to tune via env vars. Iterate in v0.2.1 if eval scores are poor.

---

## Task breakdown for Claude Code

Tasks are ordered — each one builds on the previous. Do not skip ahead. Commit at the end of each task.

---

### T1 — Migration + schema (estimated: small)

**What:** Land migration 002 and the DB migration system.

Files to create:
- `scripts/migrations/002_phase_c.sql` — exact SQL from the spec (chunks, embeddings via sqlite-vec, claims stub, claim_sources, migrations table)
- `scripts/migrate.py` — reads `scripts/migrations/*.sql` in version order, checks `migrations` table before applying, idempotent

Files to modify:
- `pyproject.toml` — add `sqlite-vec`, `anthropic`, `openai`, `trafilatura` with version pins

Tests to add:
- `tests/test_migrations.py` — apply 002 to fresh DB, verify all tables exist, verify idempotency (apply twice = no error)

Acceptance:
- `uv run python scripts/migrate.py` applies cleanly to a fresh DB and to the existing vault DB
- Idempotent: running twice does not raise
- `chunks`, `embeddings`, `claims`, `claim_sources`, `migrations` tables all exist after migration

---

### T2 — Chunker (estimated: small)

**What:** HTML → plain text → chunks with char offsets.

Files to create:
- `lib/__init__.py` (empty, if not present)
- `lib/chunker.py` — `extract_text(html: str) -> str` (trafilatura + BS4 fallback), `chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[Chunk]`, sentence-boundary-respecting split, Chunk dataclass with `text`, `char_start`, `char_end`, `ordinal`
- `tests/fixtures/sample_artifact.html` — a representative HTML page (use one of the existing vault HTML files, copied in)
- `tests/test_chunker.py` — extraction correctness, chunk boundary conditions, char offsets round-trip, sentence not split mid-sentence

Files to modify:
- None

Acceptance:
- `uv run pytest tests/test_chunker.py` — all pass
- `extract_text` returns non-empty string for `sample_artifact.html`
- Chunk `char_start` + `len(text)` == `char_end` for every chunk
- No chunk exceeds `chunk_size + max_sentence_length` chars

---

### T3 — Ingest integration (estimated: small)

**What:** Wire chunker into `scripts/ingest.py` so every new artifact is chunked at ingest time.

Files to modify:
- `scripts/ingest.py` — after `INSERT OR REPLACE INTO artifacts`, call `chunk_and_store(conn, artifact_id, html_path)` which reads the HTML, extracts text, generates chunks, inserts rows into `chunks` table (upsert on `artifact_id, ordinal`)
- `lib/db.py` (new) — extract shared DB open/path logic from `ingest.py` into a module both `ingest.py` and `embed.py` can import. Keep `ingest.py` working — this is a refactor, not a rewrite.

Acceptance:
- Existing 37 pytest tests still pass
- Re-running ingest on an existing slug updates chunks, does not duplicate
- After ingest, `SELECT COUNT(*) FROM chunks WHERE artifact_id = ?` returns > 0

---

### T4 — Embed pipeline (estimated: medium)

**What:** `scripts/embed.py` — reads un-embedded chunks, calls OpenAI, writes to `embeddings`.

Files to create:
- `scripts/embed.py` — `--incremental` (default), `--rebuild` (drop + re-embed with confirmation), batch 64 chunks/call, exponential backoff on rate limits, progress output `embedded N/M chunks (X%)`
- `lib/provider.py` — `Provider` Protocol, `ChatMessage`, `Citation`, `ChatResponse` dataclasses, `AnthropicProvider`, `OpenAIProvider`. Key validation at startup. Provider selected via `EVO_LLM_PROVIDER` env var.
- `tests/test_embed.py` — incremental mode, idempotency, rebuild flag, batch behaviour. Use `MockProvider` (no real API calls in CI).
- `tests/test_provider.py` — mock provider for all higher-level tests; real provider gated behind `RUN_LIVE_LLM=1`

Files to modify:
- `pyproject.toml` — confirm `openai` and `anthropic` are present (from T1)

Acceptance:
- `uv run scripts/embed.py --rebuild` embeds all existing artifact chunks
- `uv run scripts/embed.py` (incremental) is a no-op when all chunks are already embedded
- `SELECT COUNT(*) FROM embeddings` == `SELECT COUNT(*) FROM chunks` after rebuild
- No real API calls in `uv run pytest` (MockProvider intercepts)

---

### T5 — Retrieval (estimated: medium)

**What:** `lib/retrieve.py` — hybrid vector + FTS5 via RRF.

Files to create:
- `lib/retrieve.py` — `hybrid_retrieve(db, query, provider, k=8)` returning `list[ChunkResult]`. Vector arm: embed query → cosine search via sqlite-vec. FTS arm: `_fts_escape(query)` → BM25 on `artifacts_fts`. Merge via RRF (`k=60`). `ChunkResult` dataclass: `chunk_id`, `artifact_id`, `artifact_slug`, `artifact_title`, `text`, `char_start`, `char_end`, `score`, `source`.
- `lib/prompts.py` — `build_system_prompt(chunks: list[ChunkResult]) -> str`, numbered context blocks, "cite as [N]" instruction, "say I don't know if not in corpus" guardrail
- `tests/fixtures/eval_questions.json` — 20 questions paired with expected artifact slugs (write these from the existing 7 artifacts in the vault — questions should be answerable from the corpus)
- `tests/test_retrieve.py` — vec-only, fts-only, hybrid, top-K cap, empty-query handling. MockProvider returns fixed-size random vectors for testing (consistent seed).

Acceptance:
- All `tests/test_retrieve.py` pass
- Hybrid returns ≤ k results
- Each result has all fields populated
- FTS arm still works if sqlite-vec is unavailable (graceful fallback, log warning)

---

### T6 — Chat API (estimated: medium)

**What:** `POST /api/chat` in the Next.js portal.

Files to create:
- `scripts/chat_server.py` — FastAPI app with `POST /chat` endpoint: validates query, calls `hybrid_retrieve`, calls `Provider.chat()`, returns `ChatResponse` shape. Bind to `localhost:8765` (configurable via `EVO_CHAT_PORT`). Startup validates API keys and loads sqlite-vec extension.
- `portal/app/api/chat/route.ts` — thin proxy: forwards request body to `http://localhost:${EVO_CHAT_PORT}/chat`, surfaces errors cleanly (503 if server not running, with helpful message)
- `portal/lib/chat-client.ts` — typed `POST /api/chat` helper for the UI
- `portal/__tests__/api/chat.test.ts` — happy path, empty query rejection, provider failure handling, citation parsing

**Architecture note for Claude Code:** The portal is TypeScript (Next.js) and the retrieval/embedding logic is Python. Two options:
1. Portal calls Python via `child_process.spawn('uv', ['run', 'python', '-c', ...])` — ~300–600ms cold Python startup *per request*, before retrieval or LLM generation even starts
2. Lightweight Python HTTP server (`scripts/chat_server.py`) the portal proxies — ~10ms latency, decoupled, easy to test

**Hermes decision: Option 2 for v0.2.0.** Ship `scripts/chat_server.py` as a FastAPI app (~40 lines). Run it alongside the portal via `bun dev` using `concurrently` in `package.json`. The "more complex" framing overstates the lift — a FastAPI server with one POST endpoint is straightforward. Daily use friction matters; 600ms cold startup on every message is not acceptable for a tool you want to reach for constantly.

Files to modify:
- `portal/lib/db.ts` — add prepared statements for chunk reads by artifact_id
- `portal/package.json` — add `concurrently` dev dep; update `dev` script to `concurrently "next dev" "uv run python scripts/chat_server.py"`
- `pyproject.toml` — add `fastapi`, `uvicorn` alongside the existing new deps

Acceptance:
- `POST /api/chat` with `{"query": "what is EvoResearch?"}` returns a response with `text` (non-empty) and `citations` (array, may be empty if corpus doesn't have it)
- Invalid requests (empty query, missing body) return 400
- All `chat.test.ts` tests pass

---

### T7 — Chat UI (estimated: medium)

**What:** `/chat` route in the portal with sidebar layout.

Files to create:
- `portal/app/chat/page.tsx` — layout: left panel (cited artifacts), right panel (chat). Uses `ChatPanel` and `CitationBadge`.
- `portal/components/chat-panel.tsx` — message history, input box, submit handler, loading + error states
- `portal/components/chat-message.tsx` — renders `text` with `[N]` citations as superscript `CitationBadge` components
- `portal/components/citation-badge.tsx` — `[N]` superscript that links to `/artifacts/[slug]`

Files to modify:
- `portal/app/layout.tsx` — add `/chat` nav link alongside the existing layout

Acceptance:
- `/chat` renders without errors
- Typing a question and submitting shows a loading state, then the answer
- Citations appear as `[1]`, `[2]` superscripts inline in the answer
- Clicking a citation navigates to the source artifact page
- No regressions in grid, search, or artifact viewer

---

### T8 — Eval + hardening (estimated: small)

**What:** Smoke-test the eval set, confirm retrieval is functional, fix anything broken.

**Eval bar for v0.2.0:** 7 artifacts is too few for a meaningful 20-question set — questions degenerate into "does retrieval work at all" with no signal on hybrid vs FTS-only quality. The ≥80% top-3 bar from the spec is deferred to **v0.2.1** once the corpus is ≥30 artifacts.

For v0.2.0, the eval gate is:
- 10 questions (instead of 20), covering all 7 existing artifacts
- Bar: retrieval returns ≥1 chunk from the expected artifact in top-5 for all 10 questions
- Hybrid vs FTS-only comparison: **deferred to v0.2.1** — corpus too small to measure meaningfully

Tasks:
- Write `tests/fixtures/eval_questions.json` with 10 questions (not 20) + expected artifact slugs
- Write `tests/test_eval.py` — gated behind `--eval` flag, not in default CI run
- Run it, confirm all 10 pass
- Final CI run — all 70 existing + new tests green

Files to modify:
- `.github/workflows/ci.yml` — confirm new test files included (not `--eval`)
- `CHANGELOG.md` — fill in `[0.2.0]` entry using the template in the spec
- `CLAUDE.md` — update "current phase" to Phase C shipped, Phase D next
- `README.md` — add chat usage, `bun dev` note (now starts both Next.js + chat server), new env vars

---

### T9 — Review, tag, ship (Hermes-owned, not Claude Code)

Hermes runs this autonomously after T8 passes. ("Evo" in earlier docs refers to Hermes acting in its PM + lifecycle role — same agent, not a separate process.)

1. Read all changed files — spot-check for spec compliance
2. Run full test suite one final time
3. Samuel uses chat on real corpus for 3 sessions (acceptance criterion — Hermes checks in with Samuel before tagging)
4. `git tag -a v0.2.0 -m "feat: Phase C — RAG + chat, grounded retrieval over corpus"`
5. `git push origin v0.2.0`
6. Confirm GitHub release page shows v0.2.0

---

## Checkpoints

| After | Checkpoint |
|---|---|
| T2 (chunker) | Evo reviews chunker output on a real artifact — confirm text quality before embedding costs anything |
| T5 (retrieval) | Evo reviews eval set answers — confirm retrieval is working before wiring UI |
| T7 (chat UI) | Evo reviews full end-to-end — Samuel test drive before hardening |
| T9 | Ship |

---

## Pre-flight checklist (Claude Code reads before starting T1)

- [ ] `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` are in `.env.local` (portal) and OS env (brain)
- [ ] `uv run pytest` passes (37 tests green) — baseline before any changes
- [ ] `bun test` in `portal/` passes (33 tests green) — baseline
- [ ] Existing vault DB is backed up: `cp manifest.db manifest.db.bak` — **`scripts/migrate.py` will error if `manifest.db.bak` is missing or older than `manifest.db`** (`--require-backup` flag enforced by default; override with `--skip-backup-check` only in CI)
- [ ] `uv sync` after adding new deps to `pyproject.toml`

---

## What Claude Code must not do

- Do not modify the existing `artifacts` table schema — additive only
- Do not write to the vault DB from the portal (portal stays read-only)
- Do not add new UI dependencies — use existing shadcn/ui primitives
- Do not skip the `claims` + `claim_sources` stub tables — they must land in migration 002 even with no extraction logic
- Do not commit with phase-tracking messages ("T1 complete", "Phase C done") — describe what changed
- Do not deviate from the Provider abstraction — no raw `anthropic.Anthropic()` calls outside `lib/provider.py`
- Do not add telemetry, remote logging, or any call that leaves the machine except to LLM providers
- Do not manually delete artifacts from the DB — the existing `archived` flow (Phase D) handles cleanup. `ON DELETE CASCADE` on chunks/embeddings handles it automatically when an artifact row is deleted; confirm this is wired correctly in `test_migrations.py`
