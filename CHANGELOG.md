# Changelog

All notable changes to EvoResearch are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

---

## [0.2.0] - 2026-05-29

### Added — Phase C: Intelligence Layer

- `scripts/migrations/002_phase_c.sql` — `chunks`, `embeddings` (sqlite-vec `vec0`), `claims` stub, `claim_sources`, and `migrations` tracking tables
- `scripts/migrate.py` — forward-only migration runner with backup enforcement and sqlite-vec loading
- `lib/chunker.py` — sentence-boundary-respecting text splitter (`chunk_size=800`, `overlap=100`); trafilatura extraction with BS4 fallback
- `scripts/ingest.py` patched — `chunk_and_store()` runs automatically on every artifact ingest; re-ingest is idempotent
- `lib/provider.py` — `Provider` protocol with `BedrockProvider` (boto3); Claude Sonnet 4.6 for chat, Cohere Embed v4 at 1024 dims for embeddings; `get_provider()` factory; provider swappable via `EVO_LLM_PROVIDER` env var (default `bedrock`)
- `scripts/embed.py` — incremental (default) and rebuild embed pipeline; batch size 64; exponential backoff on rate limits; progress output
- `lib/retrieval.py` — `fts_search` (BM25 over FTS5), `vec_search` (sqlite-vec cosine), `hybrid_search` (sequential merge, dedup by chunk_id, `match_type` tagging)
- `chat_server.py` — FastAPI server on `EVO_CHAT_PORT` (default 8765); `POST /chat` embeds query → hybrid retrieval → Bedrock generation → answer + sources; `GET /health` reports corpus stats; DB opened once at startup via lifespan
- `portal/lib/chat.ts` — typed chat client (`ChatRequest`, `ChatSource`, `ChatResponse`); throws on non-200 with error passthrough
- `portal/app/chat/page.tsx` — chat UI: query input, answer prose, source list with `match_type` badges and scores; dark/light theme aware
- `scripts/eval.py` — 10-question retrieval smoke test; exits 0 if ≥8/10 questions return at least one result; retrieval-only (no generation cost)

### New commands

```bash
uv run scripts/migrate.py              # apply pending migrations
uv run scripts/embed.py --incremental  # embed new chunks only (default)
uv run scripts/embed.py --rebuild      # re-embed all chunks
uv run scripts/eval.py                 # run retrieval smoke test
uvicorn chat_server:app --port 8765    # start chat server
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
- `EVO_RESEARCH_STORE` env var for vault path override (used by tests and CI)
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

[Unreleased]: https://github.com/samueldanso/evo-research/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/samueldanso/evo-research/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/samueldanso/evo-research/releases/tag/v0.1.0
