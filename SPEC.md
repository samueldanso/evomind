# SPEC — EvoResearch System Specification

> The master technical spec for EvoResearch. For product vision and rationale, read [VISION.md](./VISION.md). For phase plan and release versions, read [ROADMAP.md](./ROADMAP.md). For the current phase under active development, read the matching doc in [`specs/`](./specs/).

## Architectural framing

**EvoResearch is an agentic system with a chat control surface — not a chatbot.** The brain (Python) runs ingest, embedding, reconciliation, and agent orchestration. The portal (TypeScript) is a thin surface over the brain. Chat is one of several control surfaces; search, browse, and agent invocation are equally first-class. Background work — claim extraction, contradiction detection, supersession — runs without user invocation as new material arrives.

Implication for implementation: do not over-invest in the chat UI as if it were the headline feature. Build chat to a polished but minimal bar; reserve UX investment for the surfaces that show the _system working on your behalf_ — contradiction queues, agent run history, the corpus growing and reorganizing itself.

## Status

| Component                       | Version | Status                                                                  |
| ------------------------------- | ------- | ----------------------------------------------------------------------- |
| Brain (Python)                  | v0.1.0  | Shipped — Phase A complete                                              |
| Portal (Next.js)                | v0.1.0  | Shipped — Phase B complete                                              |
| Intelligence layer (RAG + chat) | —       | Spec only — Phase C, see [specs/phase-c-rag.md](./specs/phase-c-rag.md) |
| Reconciliation                  | —       | Roadmap only — Phase E                                                  |
| Agentic research                | —       | Roadmap only — Phase F                                                  |

## High-level architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                          Vault (Store)                            │
│   manifest.db  (SQLite + FTS5 + sqlite-vec from Phase C)          │
│   html/        (permanent HTML artifacts)                         │
│   summaries/   (companion .md notes, Obsidian-linkable)           │
│   pdfs/        (Phase D)                                          │
│   sources/     (Phase D — raw imports awaiting normalisation)     │
└──────────────────────────────────────────────────────────────────┘
                              ▲
                              │ reads/writes
                              │
       ┌──────────────────────┴──────────────────────┐
       │                                              │
┌──────┴────────┐                              ┌──────┴────────┐
│   Brain       │                              │   Portal      │
│  (Python)     │                              │  (Next.js)    │
│               │                              │               │
│ ingest CLI    │                              │ card grid     │
│ embed worker  │                              │ search        │
│ reconciler    │                              │ artifact view │
│ agent runtime │                              │ chat UI       │
│   (E, F)      │                              │ recon UI (E)  │
└───────────────┘                              └───────────────┘
       │                                              │
       └──────────────────┬───────────────────────────┘
                          │
                  ┌───────┴────────┐
                  │  LLM Provider  │   abstracted from v0.2.0
                  │  (Anthropic    │
                  │   default)     │
                  └────────────────┘
```

**Hard rule:** the vault is the single source of truth. Both Brain and Portal read from and write to `manifest.db` directly. There is no separate database service.

---

## Layers

### 1. Storage layer — Vault + SQLite

**Default path** (macOS, Samuel):

```
~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Samuel's Vault/HomeOS/Knowledge/Research/
```

**Override:** `EVO_RESEARCH_STORE` env var. From Phase G, the path is selected by a first-run wizard with no hardcoded default beyond `~/.evoresearch/`.

**Directory layout:**

```
{STORE}/
├── manifest.db        # SQLite — single DB for all metadata, FTS, vectors, claims
├── html/              # Phase A — permanent HTML artifacts
├── summaries/         # Phase A — companion .md
├── pdfs/              # Phase D — ingested PDFs
├── md/                # Phase D — ingested raw markdown
└── sources/           # Phase D — raw imports pre-normalisation (URLs cached, etc.)
```

### 2. Brain layer — Python

Single-binary tool driven by `uv`. No external service. Stdlib + `sqlite-vec` (Phase C) + an LLM client (Phase C).

**Scripts** (`scripts/`):

- `ingest.py` — current. Phase A complete.
- `embed.py` — Phase C. Embeds new chunks, writes to `embeddings`.
- `reconcile.py` — Phase E. Runs claim extraction + contradiction detection.
- `agent.py` — Phase F. Spawns sub-agents.

**All scripts share:** `lib/db.py` (DB connection, schema, migrations), `lib/provider.py` (LLM abstraction, Phase C+), `lib/store.py` (vault paths and file IO).

### 3. Portal layer — Next.js

Local web app, reads from the vault. Next.js 16 + React 19 + Tailwind v4 + shadcn/ui + Biome + bun. `better-sqlite3` for DB access.

**Routes:**

- `/` — card grid (Phase B ✅)
- `/artifacts/[slug]` — artifact viewer (Phase B ✅)
- `/chat` — chat with KB (Phase C)
- `/reconcile` — surface contradictions (Phase E)
- `/agents` — agent run history (Phase F)

**API routes:**

- `GET /api/artifacts` ✅
- `GET /api/artifacts/[slug]` ✅
- `GET /api/artifacts/[slug]/html` ✅
- `GET /api/search?q=` ✅
- `POST /api/chat` — Phase C
- `GET /api/claims` — Phase E
- `POST /api/claims/[id]/resolve` — Phase E
- `POST /api/agents/spawn` — Phase F
- `GET /api/agents/runs/[id]` — Phase F

### 4. LLM provider layer

Introduced in Phase C. Every LLM call goes through the `Provider` interface:

```python
# lib/provider.py
class Provider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...
    def chat(self, messages: list[Message], tools: list[Tool] | None = None) -> ChatResponse: ...
```

Implementations:

- `AnthropicProvider` — default, Claude API
- `OpenAIProvider` — optional alternative
- `LocalProvider` — Phase G optional, runs nomic + a local LLM

Provider chosen via `EVO_LLM_PROVIDER` env var. API keys via `.env.local`, never committed.

### 5. Agent runtime — Phase F

`agent.py` spawns sub-processes (not threads, for isolation) that receive a scoped task, a provider, and a `tools` allowlist. Results return as JSON, persisted to `agent_runs` table, and any new artifacts the agent produced are ingested via the existing pipeline.

Detailed agent runtime spec lands in `specs/phase-f-agents.md` when Phase F begins.

---

## Data model

### Current schema (v0.1.0)

```sql
CREATE TABLE artifacts (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  slug        TEXT UNIQUE NOT NULL,
  title       TEXT NOT NULL,
  summary     TEXT NOT NULL,
  tags        TEXT NOT NULL,       -- comma-separated
  topics      TEXT NOT NULL,       -- comma-separated
  html_path   TEXT NOT NULL,
  md_path     TEXT,
  created_at  TEXT NOT NULL,       -- ISO 8601
  updated_at  TEXT NOT NULL
);

CREATE VIRTUAL TABLE artifacts_fts USING fts5(
  slug, title, summary, tags, topics,
  content='artifacts',
  content_rowid='id'
);
-- + insert/update/delete triggers (see scripts/ingest.py)
```

### Target schema (v0.5.0)

```sql
-- Phase A ✅ (existing, with one addition)
ALTER TABLE artifacts ADD COLUMN source_type TEXT NOT NULL DEFAULT 'html';
ALTER TABLE artifacts ADD COLUMN archived INTEGER NOT NULL DEFAULT 0;
ALTER TABLE artifacts ADD COLUMN source_url TEXT;  -- Phase D, URL ingest

-- Phase C
CREATE TABLE chunks (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  artifact_id   INTEGER NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
  ordinal       INTEGER NOT NULL,    -- position within artifact
  text          TEXT NOT NULL,
  char_start    INTEGER NOT NULL,    -- offset in source for anchored citations
  char_end      INTEGER NOT NULL,
  created_at    TEXT NOT NULL,
  UNIQUE(artifact_id, ordinal)
);

-- sqlite-vec virtual table — vector similarity
CREATE VIRTUAL TABLE embeddings USING vec0(
  chunk_id INTEGER PRIMARY KEY,
  embedding FLOAT[1536]              -- model-dependent dimension
);

-- Phase C stub, populated in Phase E
CREATE TABLE claims (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  text          TEXT NOT NULL,
  canonical_id  INTEGER REFERENCES claims(id),  -- dedup pointer to canonical claim
  confidence    REAL NOT NULL DEFAULT 0.0,
  superseded_by INTEGER REFERENCES claims(id),  -- chain for evolution
  created_at    TEXT NOT NULL,
  updated_at    TEXT NOT NULL
);

CREATE TABLE claim_sources (
  claim_id    INTEGER NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
  chunk_id    INTEGER NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
  PRIMARY KEY (claim_id, chunk_id)
);

-- Phase E
CREATE TABLE contradictions (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  claim_a_id    INTEGER NOT NULL REFERENCES claims(id),
  claim_b_id    INTEGER NOT NULL REFERENCES claims(id),
  detected_at   TEXT NOT NULL,
  resolved_at   TEXT,
  resolution    TEXT,  -- 'kept_a' | 'kept_b' | 'kept_both' | 'unresolved'
  CHECK (claim_a_id < claim_b_id)  -- canonical ordering, no dupes
);

-- Phase F
CREATE TABLE agent_runs (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  agent_type    TEXT NOT NULL,        -- 'fact_check' | 'deepen' | 'reconcile'
  input_json    TEXT NOT NULL,        -- scoped task
  output_json   TEXT,
  status        TEXT NOT NULL,        -- 'pending' | 'running' | 'complete' | 'failed'
  cost_tokens   INTEGER DEFAULT 0,
  cost_usd      REAL DEFAULT 0.0,
  started_at    TEXT NOT NULL,
  completed_at  TEXT,
  error         TEXT
);
```

### Migration policy

From v0.2.0 onwards, every schema change ships with a versioned migration script in `scripts/migrations/`. Migrations are forward-only. The `migrations` table tracks applied versions:

```sql
CREATE TABLE migrations (
  version  INTEGER PRIMARY KEY,
  applied_at TEXT NOT NULL
);
```

---

## Interfaces

### CLI

**Current (v0.1.0):**

```bash
uv run scripts/ingest.py --title "..." --slug "..." --tags "..." --topics "..." --summary "..." --html /path/to/file.html
uv run scripts/ingest.py --search "keyword"
uv run scripts/ingest.py --list
```

**Phase C additions:**

```bash
uv run scripts/embed.py --rebuild         # re-embed all artifacts
uv run scripts/embed.py --incremental     # embed only new artifacts
```

**Phase D additions:**

```bash
uv run scripts/ingest.py --pdf /path/to/file.pdf ...
uv run scripts/ingest.py --url https://...
uv run scripts/ingest.py --md /path/to/file.md ...
uv run scripts/ingest.py --repo /path/to/repo
```

**Phase E additions:**

```bash
uv run scripts/reconcile.py --extract     # extract claims from new chunks
uv run scripts/reconcile.py --detect      # detect contradictions
```

**Phase F additions:**

```bash
uv run scripts/agent.py spawn fact-check --claim-id 123
uv run scripts/agent.py spawn deepen --topic "Claude Managed Agents"
uv run scripts/agent.py spawn reconcile --contradiction-id 5
```

### Web API

Phase C onwards adds POST endpoints. All API routes are local-bound until Phase G adds an auth token.

See [Architecture / Portal](#3-portal-layer--nextjs) for the full route list.

---

## Configuration

### Environment variables

| Var                      | Required                    | Default                          | Phase |
| ------------------------ | --------------------------- | -------------------------------- | ----- |
| `EVO_RESEARCH_STORE`     | no                          | macOS iCloud path                | A     |
| `ANTHROPIC_API_KEY`      | yes (if provider=anthropic) | —                                | C     |
| `OPENAI_API_KEY`         | yes (if provider=openai)    | —                                | C     |
| `EVO_LLM_PROVIDER`       | no                          | `anthropic`                      | C     |
| `EVO_EMBED_MODEL`        | no                          | `text-embedding-3-small`         | C     |
| `EVO_CHUNK_SIZE`         | no                          | `800` (chars)                    | C     |
| `EVO_CHUNK_OVERLAP`      | no                          | `100` (chars)                    | C     |
| `OPENAI_BASE_URL`        | no                          | `https://api.openai.com/v1`      | C     |
| `ANTHROPIC_BASE_URL`     | no                          | `https://api.anthropic.com`      | C     |
| `EVO_CHAT_PORT`          | no                          | `8765`                           | C     |
| `EVO_MAX_AGENT_COST_USD` | no                          | `1.00` per run                   | F     |
| `EVO_PORTAL_TOKEN`       | no                          | none (localhost-only)            | G     |

All env vars validated at startup with clear error messages — never silent fallbacks.

### `.env.local` schema

Portal reads `.env.local`. Brain reads OS env. From Phase G, both share a `.env` file at the repo root with a documented schema.

---

## Code style and conventions

Existing Phase A/B conventions remain in force:

**Python:**

- Python 3.12+, `uv` package manager
- Stdlib first; external deps must be justified in a PR
- `pathlib.Path` everywhere — never string paths
- `dataclasses` for data structures
- `argparse` for CLI (no click, typer)
- Raw SQL only — no ORM
- Errors print to stderr, exit non-zero
- Type hints required on all public functions

**TypeScript / Portal:**

- Biome for formatting and linting
- `better-sqlite3` with prepared statements
- Read-only DB connection in the portal (writes go through Brain)
- Server components by default; client components only when interactive
- shadcn/ui base + Vercel AI Elements (installed via `npx shadcn`, source lands in repo); no other UI libraries
- Vercel AI SDK (`ai`, `@ai-sdk/anthropic`, `@ai-sdk/react`) for LLM streaming in the portal; no direct Anthropic SDK calls from TypeScript
- Tailwind v4

**General:**

- No hardcoded home directories — `Path.home()` or env var
- Atomic DB operations always
- FTS triggers and vec sync must be exercised by tests
- Run `uv run pytest && cd portal && bun test && bun run build` before every commit

---

## Testing strategy

### Phase A ✅

37 pytest tests, 100% coverage of `ingest.py`.

### Phase B ✅

33 vitest tests covering all API routes and grid behaviour.

### Phase C target

- 20+ pytest tests for chunking, embedding, retrieval ranking
- 15+ vitest tests for chat route and chat UI
- Smoke-test eval set: 10 questions with known-good artifact slugs, retrieval must return correct artifact in top-5 for all 10. Hybrid-vs-FTS comparison deferred to v0.2.1 (7-artifact corpus too small to measure meaningfully)

### Phase E target

- Hand-built contradiction set: 10 artifact pairs with known conflicts, detector must catch ≥ 8

### Phase F target

- Mock LLM in test mode; agents must complete deterministic test scenarios

### CI

- pytest + vitest + `bun run build` gate on every push
- Coverage reports uploaded
- From Phase G, a Docker build job runs in CI

---

## Security and privacy

**Phase A/B:**

- Path confinement on every filesystem access (`assertInsideVault`)
- CSP `script-src 'none'` on served HTML
- iframe sandbox on artifact viewer
- FTS injection protection via `_fts_escape`

**Phase C onwards:**

- API keys never logged or committed
- LLM requests and responses logged to `agent_runs` (Phase F) but redactable
- No telemetry by default; opt-in from Phase G
- Local-only by default — portal binds to 127.0.0.1
- From Phase G, single-user token protects portal if bound to non-localhost

**Phase H (v1.0):**

- Threat model documented
- Dependency vulnerability scanning in CI
- Signed releases

---

## Boundaries

**Always:**

- Run `uv run pytest` and `cd portal && bun test && bun run build` before committing
- Keep `manifest.db` inside the vault path
- Write atomic DB operations
- Generate companion `.md` for every artifact
- Reference VISION.md and ROADMAP.md in any architectural PR

**Ask first (PM gate — Hermes):**

- Adding any Python dependency beyond stdlib + already-approved (sqlite-vec, anthropic, etc.)
- Changing schema after a migration has shipped
- Moving the store path
- Adding a new phase or reordering phases
- Any change to public APIs (after Phase H / v1.0)

**Never:**

- Write to `/tmp` for research artifacts
- Hardcode Samuel's home directory
- Delete artifacts — use the `archived` flag
- Skip FTS / vec trigger setup — search and retrieval are core features
- Ship without tests
- Ship without a CHANGELOG entry
- Reproduce copyrighted content into the KB without source attribution (each chunk knows its source)

---

## Success criteria — per phase

See [ROADMAP.md](./ROADMAP.md) for acceptance criteria of each phase. The roadmap is the contract; this SPEC is the architecture that delivers on it.

---

## Open questions

These should be resolved in phase planning docs (`tasks/plan-phase-X.md`) before each phase begins. See ROADMAP.md "Open questions to resolve before each phase starts" for the per-phase list.
