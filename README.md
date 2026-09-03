# EvoMind

> AI-powered personal knowledge base with hybrid RAG retrieval, autonomous research agents, and a compounding knowledge graph.

**"The goal isn't to remember everything. It's to never lose what matters."**

## What This Demonstrates

| Capability | Implementation |
|---|---|
| **Hybrid RAG Retrieval** | Vector search (sqlite-vec, fastembed 384 dims) + FTS5 full-text search, fused via score-based merge |
| **Research Agents** | Autonomous tool-calling loop: retrieve → generate → ingest. Allowlist-enforced, fully audited. |
| **Embedding Pipeline** | Sentence-boundary chunking, batched embedding with exponential backoff, incremental + full rebuild |
| **Eval Harness** | 10-question retrieval quality gate — currently 10/10. No change ships if retrieval regresses. |
| **Provider Abstraction** | OpenRouterProvider (LLaMA 3.3 70B + fastembed) or BedrockProvider (Claude Sonnet 4.6 + Cohere Embed v4). Swappable via `EVO_LLM_PROVIDER`. |
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
│  │ Agent       │  │ (OpenRouter) │  │ Pipeline  │    │
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

**Backend:** Python 3.12+ · FastAPI · SQLite (FTS5 + sqlite-vec) · OpenRouter (LLaMA 3.3 70B) · fastembed (BAAI/bge-small-en-v1.5) · pytest (153 tests)

**Frontend:** Next.js 16 · React 19 · Tailwind v4 · shadcn/ui · better-sqlite3

## Run Locally

### Prerequisites
- Python 3.12+, [uv](https://docs.astral.sh/uv/)
- Node.js 20+, [bun](https://bun.sh)
- [OpenRouter API key](https://openrouter.ai/keys) (free)

### Backend
```bash
# Seed the database (creates demo data + embeddings)
uv run scripts/seed.py

# Start server
OPENROUTER_API_KEY=your-key-here uvicorn server:app --port 8765
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

## License

MIT
