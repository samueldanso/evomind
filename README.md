# NeuroWiKi

> AI-powered personal knowledge base with hybrid RAG retrieval, autonomous research agents, and a compounding knowledge graph.

**"The goal isn't to remember everything. It's to never lose what matters."**

## What This Demonstrates

| Capability | Implementation |
|---|---|
| **Hybrid RAG Retrieval** | Vector search (sqlite-vec, Cohere Embed v4 at 1024 dims) + FTS5 full-text search, fused via score-based merge |
| **Research Agents** | Autonomous tool-calling loop: retrieve → generate → ingest. Allowlist-enforced, fully audited. |
| **Embedding Pipeline** | Sentence-boundary chunking, batched embedding with exponential backoff, incremental + full rebuild |
| **Eval Harness** | 10-question retrieval quality gate — currently 10/10. No change ships if retrieval regresses. |
| **Provider Abstraction** | BedrockProvider (Claude Sonnet 4.6 + Cohere Embed v4). Swappable via `EVO_LLM_PROVIDER`. |
| **Migration-Versioned Schema** | Forward-only SQL migrations. SQLite + sqlite-vec + FTS5 in a single local file. |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Portal (Next.js 16, React 19, Tailwind v4)         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Landing   │  │ Wiki     │  │ Search   │          │
│  │ Page      │  │ Browser  │  │ Ask AI   │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
│       │              │              │                │
│  SQLite (readonly)   │         POST /chat            │
│  better-sqlite3      │              │                │
└──────────────────────┼──────────────┼────────────────┘
                       │              │
┌──────────────────────┼──────────────┼────────────────┐
│  Server (FastAPI)    │              │                │
│  ┌───────────────────▼──────────────▼───────────┐    │
│  │  Hybrid Retrieval: vec_search + fts_search   │    │
│  │  → score-based merge → dedup by chunk_id     │    │
│  └──────────────────────────────────────────────┘    │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────┐   │
│  │ Research    │  │ Provider     │  │ Embedding │    │
│  │ Agent       │  │ (Bedrock)    │  │ Pipeline  │    │
│  └─────────────┘  └──────────────┘  └───────────┘   │
│  ┌─────────────┐  ┌──────────────┐                   │
│  │ Tool Router │  │ Governance   │                   │
│  │ + Allowlist │  │ + Audit Log  │                   │
│  └─────────────┘  └──────────────┘                   │
└──────────────────────────────────────────────────────┘
                       │
              ┌────────▼────────┐
              │  manifest.db    │
              │  SQLite + FTS5  │
              │  + sqlite-vec   │
              └─────────────────┘
```

## Tech Stack

**Backend:** Python 3.12+ · FastAPI · SQLite (FTS5 + sqlite-vec) · AWS Bedrock (Claude Sonnet 4.6 + Cohere Embed v4) · pytest (153 tests)

**Frontend:** Next.js 16 · React 19 · Tailwind v4 · shadcn/ui · better-sqlite3

## Run Locally

### Prerequisites
- Python 3.12+, [uv](https://docs.astral.sh/uv/)
- Node.js 20+, [bun](https://bun.sh)
- AWS credentials with Bedrock access (`AWS_PROFILE` + `AWS_REGION` in env)

### Backend
```bash
# Apply migrations
uv run scripts/migrate.py

# Embed existing artifacts (if any)
uv run scripts/embed.py --incremental

# Start server
uvicorn server:app --port 8765
```

### Portal
```bash
cd portal
bun install
bun dev
```

Open `http://localhost:3000`

### Ingest research
```bash
uv run scripts/ingest.py --title "..." --slug "..." --tags "..." --topics "..." --summary "..." --html /path/to/file.html
```

### Run tests
```bash
uv run pytest                    # 153 Python tests
cd portal && bun test            # Portal tests
cd portal && bun run build       # Build check
uv run scripts/eval.py           # Retrieval quality gate (10/10)
```

## License

MIT
