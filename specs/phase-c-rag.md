# Phase C — Intelligence Layer (RAG + Chat)

> **STATUS: ✅ SHIPPED as v0.2.0** (May 31, 2026).
>
> This document is the spec for what shipped in v0.2.0 — the intelligence substrate (provider abstraction, hybrid retrieval, embedding pipeline, eval harness, chat surface). It is kept for historical reference and as documentation of what the Phase D agent layer runs on top of.
>
> In v0.3.0, this substrate is reframed: the retrieval pipeline becomes the `retrieve` tool agents call, the Provider abstraction becomes the `generate` tool, and the chat surface becomes the secondary interface for querying what agents built. No code from this phase is thrown away — it all becomes substrate the agent layer uses.
>
> For the Phase D agent runtime spec, see [phase-d-agent-foundation.md](./phase-d-agent-foundation.md).


> Target release: **v0.2.0**. This is the immediate next phase. Hermes plans, Claude Code executes.

## Objective

Make every artifact queryable via natural-language chat with grounded, cited retrieval. Lay the schema foundation for claim-level reasoning that lands in Phase E.

## Out of scope

- Multi-source ingest (still HTML only in C — that's Phase D)
- Claim extraction (table exists but no extraction logic — Phase E)
- Agent spawning (Phase F)
- Contradiction surfacing UI (Phase E)
- Cost dashboarding (defer to a later patch release if needed)

## Architecture

```
Ingest (existing) ──► artifacts table
                      │
                      ▼
                  chunker (new)
                      │
                      ▼
                  chunks table
                      │
                      ▼
                  embed worker (new)
                      │
                      ▼
                  embeddings (sqlite-vec)

Chat UI ──► POST /api/chat ──► retriever (new, hybrid: vec + fts5)
                                  │
                                  ▼
                              Provider.chat(messages, context)
                                  │
                                  ▼
                              grounded response + citations
```

## Dependencies (new)

Python:
- `sqlite-vec` — vector extension for SQLite
- `boto3` — AWS SDK for Bedrock (Claude Sonnet 4.6 + Cohere Embed v4)

TypeScript:
- No new portal deps required (chat is fetch + state)

All new deps must be added to `pyproject.toml` with justification commit.

> **What actually shipped:** `anthropic` and `openai` were originally listed but replaced by `boto3` before release (commits `59989c0`, `87a8fe2`). Only `sqlite-vec`, `boto3`, `trafilatura`, `beautifulsoup4`, `fastapi`, and `uvicorn` are in the shipped `pyproject.toml`.

## Schema additions

```sql
-- Migration 002 (Phase C)
CREATE TABLE chunks (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  artifact_id   INTEGER NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
  ordinal       INTEGER NOT NULL,
  text          TEXT NOT NULL,
  char_start    INTEGER NOT NULL,
  char_end      INTEGER NOT NULL,
  created_at    TEXT NOT NULL,
  UNIQUE(artifact_id, ordinal)
);

CREATE INDEX idx_chunks_artifact ON chunks(artifact_id);

-- sqlite-vec virtual table
CREATE VIRTUAL TABLE embeddings USING vec0(
  chunk_id INTEGER PRIMARY KEY,
  embedding FLOAT[1024]
);

-- Stub for Phase E (no extraction logic in C, but schema lands now)
CREATE TABLE claims (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  text          TEXT NOT NULL,
  canonical_id  INTEGER REFERENCES claims(id),
  confidence    REAL NOT NULL DEFAULT 0.0,
  superseded_by INTEGER REFERENCES claims(id),
  created_at    TEXT NOT NULL,
  updated_at    TEXT NOT NULL
);

CREATE TABLE claim_sources (
  claim_id    INTEGER NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
  chunk_id    INTEGER NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
  PRIMARY KEY (claim_id, chunk_id)
);

-- Migration tracking
CREATE TABLE IF NOT EXISTS migrations (
  version INTEGER PRIMARY KEY,
  applied_at TEXT NOT NULL
);
```

Migration script: `scripts/migrations/002_phase_c.sql`. Idempotent — uses `CREATE TABLE IF NOT EXISTS` and checks `migrations` before applying.

## Chunking strategy (v1, conservative)

- Strip HTML → plain text using a deterministic extractor (recommend `trafilatura` for HTML; fallback to BeautifulSoup `get_text(separator=" ")`)
- Chunk at `EVO_CHUNK_SIZE` characters (default 800) with `EVO_CHUNK_OVERLAP` overlap (default 100)
- Honor sentence boundaries — never split mid-sentence; if a sentence exceeds chunk size, that's a single chunk
- `char_start` and `char_end` are offsets in the **extracted plain text**, not the raw HTML, for citation anchoring

Hermes decides before implementation: is semantic chunking (e.g. via headings) worth the complexity in v0.2.0? Default: no — ship fixed-size, iterate later.

## Embedding pipeline

`scripts/embed.py`:

- `--incremental` (default) — embeds chunks where `chunk_id` is not yet in `embeddings`
- `--rebuild` — drops `embeddings`, re-embeds everything (with confirmation prompt)
- Batches 64 chunks per API call
- Retries with exponential backoff on rate limits
- Prints progress: `embedded 64/200 chunks (32%)`
- On failure, partial state is fine — incremental run picks up where it left off

Embedding model: `cohere.embed-v4:0` (Cohere Embed v4 via Bedrock) at 1024 dimensions. If the model changes, a full `--rebuild` is required.

> **What actually shipped:** OpenAI `text-embedding-3-small` was the original plan; shipped with Cohere Embed v4 via Bedrock instead. `EVO_EMBED_MODEL` env var was dropped — model is hardcoded in `BedrockProvider`.

## Provider abstraction

`core/llm/bedrock.py`:

```python
from typing import Protocol, Iterable
from dataclasses import dataclass

@dataclass
class ChatMessage:
    role: str       # 'system' | 'user' | 'assistant'
    content: str

@dataclass
class Citation:
    chunk_id: int
    artifact_id: int
    excerpt: str    # ≤ 200 chars

@dataclass
class ChatResponse:
    text: str
    citations: list[Citation]
    cost_tokens: int
    cost_usd: float

class Provider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...
    def chat(self, messages: list[ChatMessage], context_chunks: list[dict]) -> ChatResponse: ...
```

Implementations in C (shipped):
- `BedrockProvider` — boto3 client; Claude Sonnet 4.6 for chat, Cohere Embed v4 (1024 dims) for embeddings

Provider selection at startup via `EVO_LLM_PROVIDER` (default `bedrock`). AWS credentials validated at client creation time (boto3 raises if profile/region invalid).

> **What actually shipped:** The original plan had `AnthropicProvider` + `OpenAIProvider`. These were implemented and then replaced by `BedrockProvider` before release (commits `87a8fe2`, `59989c0`). Only `bedrock` is a valid provider value.

## Retrieval

`core/memory/retrieval.py`:

```python
def hybrid_retrieve(
    db: sqlite3.Connection,
    query: str,
    provider: Provider,
    k: int = 8,
) -> list[ChunkResult]:
    """Hybrid retrieval: vector + FTS5, merged with score-based dedup."""
```

- Vector arm — embed query, top-K from `embeddings` via `sqlite-vec` cosine
- FTS arm — `_fts_escape(query)` against `artifacts_fts`, top-K by BM25
- Merge — sequential score-based dedup (take higher score per chunk_id, mark `match_type` as `hybrid`), return top-K sorted by score
- Each result includes: `chunk_id`, `artifact_id`, `text`, `score`, `source` (`'vec' | 'fts' | 'both'`)

## Chat API

`POST /api/chat` request shape:

```typescript
{
  query: string;
  history?: ChatMessage[];  // optional prior turns
  k?: number;               // override default retrieval depth
}
```

Response shape:

```typescript
{
  text: string;
  citations: Array<{
    chunk_id: number;
    artifact_id: number;
    artifact_slug: string;
    artifact_title: string;
    excerpt: string;
    char_start: number;
    char_end: number;
  }>;
  cost_tokens: number;
  cost_usd: number;
}
```

Server-side flow:
1. Validate query (non-empty, length cap)
2. Call `hybrid_retrieve` → top-K chunks
3. Build system prompt with retrieved chunks formatted as numbered context blocks
4. Call `Provider.chat()` with the formatted prompt
5. Parse model output to extract citation references (model is instructed to cite as `[1]`, `[2]`, etc.)
6. Return response

System prompt template (in `core/prompts/`):

```
You are EvoResearch, a research assistant grounded in Samuel's research corpus.

Use the numbered context blocks below to answer the question. Cite every factual claim with [N] referring to a context block. If the corpus does not contain an answer, say so explicitly — do not guess.

Context:
{numbered_blocks}

Question: {query}
```

## Chat UI

New route: `/chat`.

- Sidebar layout — chat on the right, source panel on the left showing cited artifacts
- Input box at bottom, message history above
- Each message renders citations as numbered superscripts; clicking opens the cited artifact at the chunk position
- Use existing shadcn/ui primitives — no new UI dependencies
- Loading state during retrieval + generation
- Error state with retry button on API failures
- Streaming response (if Anthropic SDK supports it) is nice-to-have, not required for v0.2.0

## Files to create

```
scripts/
  embed.py                          (new)
  migrations/
    002_phase_c.sql                 (new)
core/
  __init__.py
  llm/
    __init__.py
    bedrock.py                      (Provider protocol + BedrockProvider)
  memory/
    __init__.py
    db.py                           (shared DB helpers extracted from ingest.py)
    retrieval.py                    (hybrid retrieval)
    chunker.py                      (HTML extraction + chunking)
tests/
  test_chunker.py                   (new)
  test_embed.py                     (new)
  test_retrieve.py                  (new)
  test_provider.py                  (new — with mock provider)
  fixtures/
    sample_artifact.html            (new)
    eval_questions.json             (new — 20-question eval set)
portal/
  app/
    chat/
      page.tsx                      (new)
    api/
      chat/
        route.ts                    (new)
  components/
    chat-panel.tsx                  (new)
    chat-message.tsx                (new)
    citation-badge.tsx              (new)
  lib/
    chat-client.ts                  (new — POST /api/chat helper)
  __tests__/
    api/
      chat.test.ts                  (new)
```

## Files to modify

```
scripts/ingest.py                   — after ingest, trigger chunker
pyproject.toml                      — add sqlite-vec, anthropic, openai, trafilatura
CHANGELOG.md                        — Phase C entry under [Unreleased]
CLAUDE.md                           — update "current phase" section
portal/package.json                 — no new deps expected
portal/lib/db.ts                    — extend prepared statements for chunks
portal/app/layout.tsx               — add /chat nav link
```

## Configuration additions

`.env.local` (portal) and OS env (brain) gain:

```bash
AWS_PROFILE=my-bedrock-profile   # or valid AWS credentials
AWS_REGION=us-east-1             # Bedrock region
EVO_LLM_PROVIDER=bedrock         # 'bedrock' (only implemented provider)
EVO_CHUNK_SIZE=800
EVO_CHUNK_OVERLAP=100
```

All new env vars validated at startup with clear errors. Default values documented in `README.md`.

## Testing

**Python (pytest):**

- `test_chunker.py` — HTML → text → chunks, boundary conditions, char offsets correct
- `test_embed.py` — incremental embedding, idempotency, batch behaviour, rebuild flag
- `test_retrieve.py` — vec-only retrieval, fts-only retrieval, hybrid score-based merge, top-K cap
- `test_provider.py` — mock provider used in all higher-level tests; real provider gated behind `RUN_LIVE_LLM=1`
- Coverage: new modules at 100%, retrieval at ≥ 95%

**TypeScript (vitest):**

- `chat.test.ts` — happy path, empty query rejection, retrieval failure handling, citation parsing

**Eval set:**

- 10 questions hardcoded in `scripts/eval.py` (no separate JSON fixture file)
- Run via `uv run scripts/eval.py` — retrieval-only, no generation cost
- Bar: ≥ 8/10 questions return at least one result (`PASS_THRESHOLD = 8`); currently 10/10 on dogfood corpus

## Acceptance criteria

A Phase C release ships when **all** of the following are true:

- [ ] Migration 002 applies cleanly to a fresh DB and to the existing v0.1.0 vault
- [ ] All artifacts in the existing vault have chunks and embeddings after running `uv run scripts/embed.py --rebuild`
- [ ] `POST /api/chat` returns a grounded answer with valid citations for a sample question
- [ ] `/chat` route renders, accepts input, displays answer + citations, and clicking a citation opens the source artifact
- [ ] Hybrid retrieval beats FTS5-only on the eval set (measurable improvement, even if small)
- [ ] `claims` and `claim_sources` tables exist, no rows yet, no extraction logic shipped
- [ ] New tests pass; existing tests still pass; CI green
- [ ] No regressions in portal v0.1.0 functionality — grid, search, viewer still work
- [ ] `CHANGELOG.md` entry for v0.2.0 complete
- [ ] `CLAUDE.md` updated to reflect Phase C shipped, Phase D next
- [ ] Samuel personally uses chat on his real corpus for at least 3 sessions before tagging the release
- [ ] No telemetry, no remote logging, all traffic stays between Samuel's machine and the LLM provider

## Risks

| Risk | Mitigation |
|---|---|
| Embedding cost unbounded | Cohere Embed v4 via Bedrock; incremental mode skips re-work |
| Provider lock-in | `Provider` protocol interface from day one; new providers can implement it without touching existing code |
| sqlite-vec dimension mismatch on model change | `--rebuild` flag forces full re-embed; error message catches mismatch at startup |
| Chunk size badly chosen | Configurable via env; eval set re-runs cheaply once embedded |
| Chat hallucinates outside the corpus | System prompt explicitly forbids; "I don't know" is a valid answer |
| Portal write contention with brain | Portal stays read-only; chat doesn't write to DB (cost logs are optional Phase F concern) |

## Open questions (Hermes resolves before kickoff)

1. **Embedding provider** — OpenAI default or Voyage default? OpenAI is cheaper; Voyage is better quality. Recommend OpenAI for v0.2.0.
2. **HTML extraction library** — `trafilatura` (recommended), `readability-lxml`, or custom? Decide before chunker work begins.
3. **Streaming chat response** — ship synchronous in v0.2.0 and add streaming in v0.2.1? Recommend yes.
4. **Chat history persistence** — store conversations in DB or keep in browser state? Recommend browser state for v0.2.0; revisit when multi-device matters.
5. **Source attribution in chat** — show artifact title only, or also a short excerpt? Recommend both, with the excerpt being the ±150 chars around the citation hit.

## CHANGELOG entry template

When Phase C ships, the entry under `[0.2.0] - YYYY-MM-DD` should read:

```markdown
## [0.2.0] - YYYY-MM-DD

### Added — Phase C: Intelligence Layer

- Chunking pipeline — `core/memory/chunker.py` extracts plain text from HTML and chunks it with deterministic char-offset anchoring
- `chunks` and `embeddings` tables — `sqlite-vec` virtual table for vector similarity alongside FTS5
- `scripts/embed.py` — incremental and rebuild modes, batched embedding with retry
- `core/llm/bedrock.py` — pluggable LLM provider (BedrockProvider: Claude Sonnet 4.6 + Cohere Embed v4 via boto3)
- `core/memory/retrieval.py` — hybrid retrieval combining vector and FTS5 via score-based merge
- `POST /chat` — grounded chat over the corpus with cited responses (FastAPI at repo root)
- `/chat` route in the portal — chat UI with source list and match_type badges
- `claims` and `claim_sources` schema stubs — populated in Phase F
- Migration system — versioned forward-only SQL migrations under `scripts/migrations/`
- 10-question eval set with retrieval quality gate (≥8/10)
- New env vars: `AWS_PROFILE`, `AWS_REGION`, `EVO_LLM_PROVIDER`, `EVO_CHUNK_SIZE`, `EVO_CHUNK_OVERLAP`
- 84 pytest tests, 4 vitest tests

### Changed

- `scripts/ingest.py` now triggers chunking after artifact save
- Portal layout adds /chat link in primary navigation

### Migration notes

Run `uv run scripts/embed.py --rebuild` once after upgrading to populate embeddings for existing artifacts.
```

---

## Working agreement for Phase C

- Hermes (PM) — produces `tasks/plan-phase-c.md` and `tasks/todo-phase-c.md` resolving the open questions above before any code is written
- Claude Code (SWE) — implements per this spec; raises any architectural deviation as a question, not a silent change
- Samuel (PO) — reviews the plan-phase-c.md before implementation begins; sign-off ungated by acceptance criteria after implementation
