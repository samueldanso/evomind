# EvoMind Deployment — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make EvoMind a live, working URL — swap AWS Bedrock for OpenRouter (free) + local embeddings, deploy Python backend to Render and portal to Vercel.

**Architecture:** New `OpenRouterProvider` uses fastembed (ONNX, CPU) for local embeddings and OpenRouter API (free LLaMA 3.3 70B) for chat. Seed script expanded to create chunks + embeddings so the DB ships ready for RAG. Backend deploys to Render (Docker, persistent disk for SQLite). Portal deploys to Vercel.

**Tech Stack:** fastembed (ONNX embeddings), httpx (OpenRouter API), Render (Docker), Vercel (Next.js)

## Global Constraints

- Existing Python tests (153) must still pass — do not remove BedrockProvider, add OpenRouterProvider alongside it
- Portal tests (37) must still pass, build must succeed
- No AWS credentials required for the default provider
- `EVO_LLM_PROVIDER=openrouter` is the new default; `bedrock` still works if AWS is configured
- Embedding dimension: 384 (BAAI/bge-small-en-v1.5 via fastembed)
- Chat model: `meta-llama/llama-3.3-70b-instruct:free` via OpenRouter
- DB path in Docker: `/data/manifest.db` on a Render persistent disk
- CORS in production: allow the Vercel domain

---

### Task 1: OpenRouter Provider

**Files:**
- Create: `core/llm/openrouter.py`
- Modify: `core/llm/__init__.py`
- Modify: `core/llm/bedrock.py` (only `get_provider()` function)
- Modify: `pyproject.toml` (add httpx + fastembed deps, make boto3 optional)

**Interfaces:**
- Produces: `OpenRouterProvider` class implementing `Provider` protocol (same `embed()` and `chat()` signatures as `BedrockProvider`). `get_provider()` returns `OpenRouterProvider` when `EVO_LLM_PROVIDER=openrouter` (new default).

- [ ] **Step 1: Add dependencies**

```bash
uv add httpx fastembed
```

Move `boto3` from required to optional — it's only needed for BedrockProvider:

In `pyproject.toml`, change `dependencies`:
```toml
dependencies = [
    "sqlite-vec>=0.1.6",
    "trafilatura>=2.0.0",
    "beautifulsoup4>=4.13.0",
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "httpx>=0.27.0",
    "fastembed>=0.6.0",
]
```

(boto3 is already a dev dep via httpx tests — BedrockProvider does a lazy `import boto3` with a helpful error, so it still works if installed)

- [ ] **Step 2: Create OpenRouter provider**

Create `core/llm/openrouter.py`:

```python
"""OpenRouter provider — free LLaMA chat + local fastembed embeddings."""

from __future__ import annotations

import os
from typing import Any

import httpx

from core.llm.bedrock import ChatMessage, ChatResponse, Citation

# Lazy-loaded fastembed model (downloaded on first use, cached after)
_embedder = None

def _get_embedder():
    global _embedder
    if _embedder is None:
        from fastembed import TextEmbedding
        _embedder = TextEmbedding("BAAI/bge-small-en-v1.5")
    return _embedder


class OpenRouterProvider:
    """Provider using OpenRouter (free LLaMA 3.3 70B) for chat and fastembed for embeddings."""

    def __init__(
        self,
        chat_model: str = "meta-llama/llama-3.3-70b-instruct:free",
        api_key: str | None = None,
    ) -> None:
        self.chat_model = chat_model
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is required. Get a free key at https://openrouter.ai/keys"
            )
        self.base_url = "https://openrouter.ai/api/v1"

    def embed(self, texts: list[str], input_type: str = "search_document") -> list[list[float]]:
        """Embed texts locally using fastembed (ONNX, CPU). No API call."""
        embedder = _get_embedder()
        embeddings = list(embedder.embed(texts))
        return [e.tolist() for e in embeddings]

    def chat(self, messages: list[ChatMessage], context_chunks: list[str]) -> ChatResponse:
        """Generate a response via OpenRouter API."""
        context_block = "\n\n---\n\n".join(context_chunks)
        user_content = f"<context>\n\n{context_block}\n\n</context>\n\n{messages[-1].content}"

        payload: dict[str, Any] = {
            "model": self.chat_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a research assistant. Answer using only the provided context chunks. Cite sources inline.",
                },
                {"role": "user", "content": user_content},
            ],
            "max_tokens": 1024,
        }

        response = httpx.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return ChatResponse(content=content, citations=[])
```

- [ ] **Step 3: Update get_provider() and __init__.py**

In `core/llm/bedrock.py`, update `get_provider()`:

```python
def get_provider(provider_name: str | None = None) -> Provider:
    name = provider_name or os.environ.get("EVO_LLM_PROVIDER", "openrouter")
    if name == "openrouter":
        from core.llm.openrouter import OpenRouterProvider
        return OpenRouterProvider()
    if name == "bedrock":
        return BedrockProvider()
    raise ValueError(f"Unknown provider: {name!r}. Expected 'openrouter' or 'bedrock'.")
```

Note: default changed from `"bedrock"` to `"openrouter"`.

In `core/llm/__init__.py`, add OpenRouterProvider to exports:

```python
from core.llm.bedrock import (
    BedrockProvider,
    ChatMessage,
    ChatResponse,
    Citation,
    Provider,
    get_provider,
)
from core.llm.openrouter import OpenRouterProvider

__all__ = [
    "BedrockProvider",
    "OpenRouterProvider",
    "ChatMessage",
    "ChatResponse",
    "Citation",
    "Provider",
    "get_provider",
]
```

- [ ] **Step 4: Update server/__init__.py to use get_provider()**

Replace the direct `BedrockProvider()` import with `get_provider()`:

```python
from core.llm.bedrock import get_provider
```

In the lifespan function, change:
```python
provider = BedrockProvider()
```
to:
```python
provider = get_provider()
```

Also update the import at the top — remove `from core.llm.bedrock import BedrockProvider`, add `from core.llm.bedrock import get_provider`.

Update CORS to allow the production Vercel domain:
```python
allow_origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    os.environ.get("ALLOWED_ORIGIN", ""),
],
```

- [ ] **Step 5: Update server/routes/chat.py**

Change the type annotation from `BedrockProvider` to a generic provider. Replace:
```python
from core.llm.bedrock import BedrockProvider, ChatMessage
```
with:
```python
from core.llm.bedrock import ChatMessage
```

And change:
```python
provider: BedrockProvider = request.app.state.provider
```
to:
```python
provider = request.app.state.provider
```

- [ ] **Step 6: Update scripts/embed.py to use get_provider()**

Replace:
```python
from core.llm.bedrock import BedrockProvider
```
with:
```python
from core.llm.bedrock import get_provider
```

Change the provider init:
```python
provider = get_provider()
```

Update the type hints from `BedrockProvider` to generic:
```python
def embed_chunks(conn, chunks, provider):
```
```python
def _embed_with_retry(provider, texts):
```
```python
def run_incremental(conn, provider):
```
```python
def run_rebuild(conn, provider):
```

- [ ] **Step 7: Run tests**

```bash
uv run pytest
```

Expected: 153 pass. The tests mock the provider or use `RUN_LIVE_LLM=1` guard, so switching the default shouldn't break anything. If any tests import `BedrockProvider` directly and fail, fix the imports.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat: add OpenRouter provider with local fastembed embeddings"
```

---

### Task 2: Expand Seed Script with Chunks + Embeddings

**Files:**
- Rewrite: `scripts/seed.py`

**Interfaces:**
- Consumes: `OpenRouterProvider.embed()` from Task 1 (or fastembed directly)
- Produces: `data/manifest.db` with artifacts + FTS5 + chunks + chunks_fts + embeddings (384-dim) — fully ready for hybrid search

- [ ] **Step 1: Rewrite seed.py**

The seed script needs to:
1. Create all tables (artifacts, FTS5, chunks, chunks_fts, embeddings with 384 dims)
2. Insert the 10 demo artifacts
3. Chunk each artifact's summary into the chunks table
4. Embed all chunks using fastembed
5. Store embeddings in the vec0 table

```python
"""Seed manifest.db with demo artifacts, chunks, and embeddings."""

import sqlite3
import struct
import sys
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "manifest.db"

EMBEDDING_DIM = 384  # BAAI/bge-small-en-v1.5

SCHEMA = """
CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    tags TEXT NOT NULL DEFAULT '',
    topics TEXT NOT NULL DEFAULT '',
    html_path TEXT,
    md_path TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE VIRTUAL TABLE IF NOT EXISTS artifacts_fts USING fts5(
    title, summary, tags, topics,
    content='artifacts', content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS artifacts_ai AFTER INSERT ON artifacts BEGIN
    INSERT INTO artifacts_fts(rowid, title, summary, tags, topics)
    VALUES (new.id, new.title, new.summary, new.tags, new.topics);
END;

CREATE TRIGGER IF NOT EXISTS artifacts_ad AFTER DELETE ON artifacts BEGIN
    INSERT INTO artifacts_fts(artifacts_fts, rowid, title, summary, tags, topics)
    VALUES ('delete', old.id, old.title, old.summary, old.tags, old.topics);
END;

CREATE TRIGGER IF NOT EXISTS artifacts_au AFTER UPDATE ON artifacts BEGIN
    INSERT INTO artifacts_fts(artifacts_fts, rowid, title, summary, tags, topics)
    VALUES ('delete', old.id, old.title, old.summary, old.tags, old.topics);
    INSERT INTO artifacts_fts(rowid, title, summary, tags, topics)
    VALUES (new.id, new.title, new.summary, new.tags, new.topics);
END;

CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_id INTEGER NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    char_start INTEGER NOT NULL DEFAULT 0,
    char_end INTEGER NOT NULL DEFAULT 0
);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    text, content='chunks', content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, text) VALUES (new.id, new.text);
END;

CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, text) VALUES ('delete', old.id, old.text);
END;
"""

# NOTE: embeddings table created separately after sqlite-vec is loaded

ARTIFACTS = [
    # ... (same 10 artifacts as before — keep the existing ARTIFACTS list)
]


def seed():
    DB_DIR.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        print(f"DB exists at {DB_PATH} — removing for fresh seed.")
        DB_PATH.unlink()

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)

    # Load sqlite-vec for embeddings table
    try:
        import sqlite_vec
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
    except Exception as exc:
        print(f"WARNING: sqlite-vec not available ({exc}). Skipping embeddings.")
        _seed_artifacts_and_chunks(conn, embed=False)
        conn.close()
        return

    conn.execute(
        f"CREATE VIRTUAL TABLE IF NOT EXISTS embeddings USING vec0(chunk_id INTEGER PRIMARY KEY, embedding float[{EMBEDDING_DIM}])"
    )

    _seed_artifacts_and_chunks(conn, embed=True)
    conn.close()


def _seed_artifacts_and_chunks(conn: sqlite3.Connection, embed: bool) -> None:
    # Insert artifacts
    for art in ARTIFACTS:
        conn.execute(
            "INSERT INTO artifacts (slug, title, summary, tags, topics, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (art["slug"], art["title"], art["summary"], art["tags"], art["topics"], art["created_at"], art["created_at"]),
        )

    conn.commit()

    # Create chunks from summaries
    artifacts = conn.execute("SELECT id, summary FROM artifacts").fetchall()
    chunk_ids_texts: list[tuple[int, str]] = []

    for art_id, summary in artifacts:
        if not summary:
            continue
        cursor = conn.execute(
            "INSERT INTO chunks (artifact_id, text, char_start, char_end) VALUES (?, ?, 0, ?)",
            (art_id, summary, len(summary)),
        )
        chunk_ids_texts.append((cursor.lastrowid, summary))

    conn.commit()
    print(f"Seeded {len(ARTIFACTS)} artifacts and {len(chunk_ids_texts)} chunks.")

    if not embed or not chunk_ids_texts:
        return

    # Embed chunks
    print("Computing embeddings with fastembed...")
    try:
        from fastembed import TextEmbedding
        embedder = TextEmbedding("BAAI/bge-small-en-v1.5")
    except ImportError:
        print("WARNING: fastembed not installed. Skipping embeddings.")
        return

    texts = [text for _, text in chunk_ids_texts]
    embeddings = list(embedder.embed(texts))

    for (chunk_id, _), embedding in zip(chunk_ids_texts, embeddings):
        blob = struct.pack(f"{len(embedding)}f", *embedding.tolist())
        conn.execute("INSERT INTO embeddings (chunk_id, embedding) VALUES (?, ?)", (chunk_id, blob))

    conn.commit()
    print(f"Embedded {len(embeddings)} chunks ({EMBEDDING_DIM} dims).")


if __name__ == "__main__":
    seed()
```

Keep the same 10 ARTIFACTS from the existing seed.py — just copy the list over.

- [ ] **Step 2: Run the seed**

```bash
rm -f data/manifest.db
uv run scripts/seed.py
```

Expected output:
```
Seeded 10 artifacts and 10 chunks.
Computing embeddings with fastembed...
Embedded 10 chunks (384 dims).
```

- [ ] **Step 3: Verify locally**

Start the FastAPI server (needs OPENROUTER_API_KEY):
```bash
OPENROUTER_API_KEY=<key> EVO_STORE=./data uvicorn server:app --port 8765
```

Test the health endpoint:
```bash
curl http://localhost:8765/health
```

Expected: `{"status": "ok", "chunk_count": 10, "embedding_count": 10}`

Test Ask AI:
```bash
curl -X POST http://localhost:8765/chat -H "Content-Type: application/json" -d '{"query": "How does hybrid search work?"}'
```

Expected: A real answer citing the seed articles.

- [ ] **Step 4: Run tests**

```bash
uv run pytest
```

Expected: 153 pass (seed doesn't affect tests — they use their own test DBs).

- [ ] **Step 5: Commit**

```bash
git add scripts/seed.py data/
git commit -m "feat: expand seed with chunks + fastembed embeddings for working RAG"
```

---

### Task 3: Dockerfile + Render Deployment

**Files:**
- Create: `Dockerfile`
- Create: `render.yaml`
- Create: `docker-entrypoint.sh`

**Interfaces:**
- Consumes: `scripts/seed.py` from Task 2, `server:app` FastAPI application
- Produces: Docker image deployable to Render with persistent disk at `/data`

- [ ] **Step 1: Create Dockerfile**

Create `Dockerfile` at project root:

```dockerfile
FROM python:3.12-slim AS base

WORKDIR /app

# System deps for sqlite-vec
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv sync --no-dev --frozen

# Pre-download fastembed model at build time (cached in image)
RUN uv run python -c "from fastembed import TextEmbedding; TextEmbedding('BAAI/bge-small-en-v1.5')"

# App code
COPY core/ core/
COPY server/ server/
COPY scripts/ scripts/

# Entrypoint seeds DB on first run if missing
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PYTHONUNBUFFERED=1
ENV EVO_STORE=/data
ENV PORT=8765

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import httpx; r = httpx.get('http://localhost:8765/health'); exit(0 if r.status_code == 200 else 1)"

ENTRYPOINT ["/entrypoint.sh"]
```

- [ ] **Step 2: Create docker-entrypoint.sh**

```bash
#!/bin/sh
set -e

# Seed DB on first run (persistent disk starts empty)
if [ ! -f /data/manifest.db ]; then
    echo "No DB found at /data/manifest.db — seeding..."
    mkdir -p /data
    uv run python scripts/seed.py
    echo "Seed complete."
fi

# Start FastAPI server
exec uv run uvicorn server:app --host 0.0.0.0 --port "${PORT:-8765}"
```

- [ ] **Step 3: Create render.yaml**

```yaml
services:
  - type: web
    name: evomind-api
    runtime: docker
    healthCheckPath: /health
    plan: starter
    disk:
      name: evomind-data
      mountPath: /data
      sizeGB: 1
    envVars:
      - key: EVO_STORE
        value: /data
      - key: PORT
        value: 8765
      - key: EVO_LLM_PROVIDER
        value: openrouter
      - key: OPENROUTER_API_KEY
        sync: false
      - key: ALLOWED_ORIGIN
        value: https://evomind.vercel.app
```

- [ ] **Step 4: Test Docker locally**

```bash
docker build -t evomind-api .
docker run --rm -p 8765:8765 -e OPENROUTER_API_KEY=<key> -v evomind-data:/data evomind-api
```

Verify:
```bash
curl http://localhost:8765/health
curl -X POST http://localhost:8765/chat -H "Content-Type: application/json" -d '{"query": "What is RAG?"}'
```

- [ ] **Step 5: Commit**

```bash
git add Dockerfile docker-entrypoint.sh render.yaml
git commit -m "feat: add Dockerfile and Render deployment config"
```

---

### Task 4: Vercel Deployment + Portal Production Wiring

**Files:**
- Create: `portal/vercel.json`
- Modify: `portal/app/api/chat/route.ts` (already exists — just verify EVO_SERVER_URL is used)
- Modify: `portal/lib/path-guard.ts` (update default path for production)
- Create: `portal/.env.example`

**Interfaces:**
- Consumes: Render backend URL from Task 3
- Produces: Portal deployable to Vercel, wired to Render backend

- [ ] **Step 1: Create vercel.json**

```json
{
  "framework": "nextjs",
  "installCommand": "bun install",
  "buildCommand": "bun run build"
}
```

- [ ] **Step 2: Create portal/.env.example**

```bash
# Backend API URL (Render deployment)
EVO_SERVER_URL=https://evomind-api.onrender.com

# Local development
# EVO_SERVER_URL=http://127.0.0.1:8765

# Vault path (local dev only — production reads from backend API)
# EVO_STORE=/path/to/data
```

- [ ] **Step 3: Update path-guard.ts for production**

The portal reads SQLite directly for the wiki/search pages. On Vercel (serverless), there's no local SQLite file. Two approaches:
- Option A: Proxy all data reads through the Python backend (big rewrite)
- Option B: Bundle a read-only copy of manifest.db with the Vercel deployment

Option B is simpler: commit a `data/manifest.db` to the repo (override the gitignore for this one file), and update path-guard to resolve relative to the project root.

Update `portal/lib/path-guard.ts`:

```typescript
import path from "node:path";

export function resolveVaultRoot(): string {
  return path.resolve(
    process.env.EVO_STORE ?? path.join(process.cwd(), "..", "data")
  );
}

export function assertInsideVault(filePath: string): string {
  const resolved = path.resolve(filePath);
  const vaultRoot = resolveVaultRoot();
  if (!resolved.startsWith(vaultRoot + path.sep)) {
    throw new Error(`Path outside vault: ${resolved}`);
  }
  return resolved;
}
```

This resolves to `<project>/data/` by default (one level up from portal/).

- [ ] **Step 4: Add data/manifest.db to git**

Add a gitignore override to track the seeded DB:

In `.gitignore`, add:
```
# Track the seeded demo DB (override *.db rule)
!data/manifest.db
```

Then:
```bash
git add -f data/manifest.db
```

- [ ] **Step 5: Verify build**

```bash
cd portal && bun run build
```

Expected: Clean build. The wiki page should pick up `../data/manifest.db`.

- [ ] **Step 6: Commit**

```bash
git add portal/vercel.json portal/.env.example portal/lib/path-guard.ts .gitignore data/manifest.db
git commit -m "feat: add Vercel deployment config, bundle seed DB"
```

---

### Task 5: Update .env.example + README + Final Verification

**Files:**
- Modify: `.env.example` (project root)
- Modify: `README.md`

**Interfaces:**
- Produces: Updated documentation with deployment instructions

- [ ] **Step 1: Update root .env.example**

```bash
# LLM Provider (default: openrouter)
EVO_LLM_PROVIDER=openrouter

# OpenRouter API key (free at https://openrouter.ai/keys)
OPENROUTER_API_KEY=

# Data path (default: ./data)
EVO_STORE=./data

# Server port
EVO_CHAT_PORT=8765

# Frontend origin (for CORS)
ALLOWED_ORIGIN=http://localhost:3000

# --- Optional: AWS Bedrock (only if EVO_LLM_PROVIDER=bedrock) ---
# AWS_PROFILE=
# AWS_REGION=us-east-1
```

- [ ] **Step 2: Update README.md**

Add a "Deployment" section and update "Run Locally" to reflect OpenRouter:

Under "Run Locally", update Prerequisites:
```markdown
### Prerequisites
- Python 3.12+, [uv](https://docs.astral.sh/uv/)
- Node.js 20+, [bun](https://bun.sh)
- [OpenRouter API key](https://openrouter.ai/keys) (free)
```

Update Backend section:
```markdown
### Backend
\```bash
# Seed the database (creates demo data + embeddings)
uv run scripts/seed.py

# Start server
OPENROUTER_API_KEY=your-key-here uvicorn server:app --port 8765
\```
```

Add Deployment section:
```markdown
## Deployment

**Backend** → [Render](https://render.com) (Docker + persistent disk)
**Frontend** → [Vercel](https://vercel.com) (Next.js)

### Deploy Backend
1. Create a new Web Service on Render
2. Connect your GitHub repo
3. Render auto-detects the `render.yaml` — confirm settings
4. Set `OPENROUTER_API_KEY` in the Render dashboard (Secrets)
5. Deploy — the entrypoint seeds the DB on first run

### Deploy Frontend
1. Import the repo on Vercel
2. Set root directory to `portal`
3. Set `EVO_SERVER_URL` to your Render backend URL (e.g., `https://evomind-api.onrender.com`)
4. Deploy
```

- [ ] **Step 3: Full verification**

```bash
# Python tests
uv run pytest

# Portal tests + build
cd portal && bun test && bun run build

# Local E2E (needs OPENROUTER_API_KEY)
OPENROUTER_API_KEY=<key> EVO_STORE=./data uvicorn server:app --port 8765 &
cd portal && bun dev
# Visit localhost:3000 — wiki shows 10 articles, Ask AI returns real answers
```

- [ ] **Step 4: Commit and push**

```bash
git add -A
git commit -m "docs: update README with deployment instructions and OpenRouter setup"
git push
```
