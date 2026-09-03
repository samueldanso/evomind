# EvoMind

Personal AI knowledge base with hybrid RAG retrieval. Ingest articles, PDFs, or URLs — ask questions and get cited answers grounded in your own research.

**[Live Demo](https://evomind-ai.vercel.app)** · **[GitHub](https://github.com/samueldanso/evomind)**

## Features

- **Hybrid Search** — every query runs vector similarity + full-text keyword search in parallel, then fuses the results for comprehensive recall
- **Cited Q&A** — ask a question in natural language, get a grounded answer with source citations and relevance scores
- **Multi-Source Ingest** — paste text, drop a URL, or upload a PDF/DOCX — content is extracted, chunked, embedded, and indexed automatically
- **Wiki Browser** — browse, search, and filter your knowledge base with instant FTS5-powered keyword search
- **Eval-Gated Quality** — a retrieval quality harness gates every change to the system; if search quality drops, the change doesn't ship

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12 · FastAPI · SQLite (FTS5 + sqlite-vec) |
| **LLM** | OpenRouter (Gemma 4 26B, free) · fastembed (local ONNX embeddings) |
| **Frontend** | Next.js 16 · React 19 · Tailwind v4 · shadcn/ui |
| **Database** | Single-file SQLite with FTS5 full-text search + sqlite-vec vector search |
| **Deployment** | Render (Docker + persistent disk) · Vercel (Next.js) |
| **Testing** | pytest (150+ tests) · Vitest · Biome |

## Architecture

```
Portal (Next.js)                     Server (FastAPI)
┌──────────────────────┐             ┌──────────────────────────┐
│  Wiki Browser        │──SQLite──→  │                          │
│  Keyword Search      │  (readonly) │  Hybrid Retrieval        │
│  Landing Page        │             │  vec_search + fts_search │
│                      │             │  → score-based merge     │
│  Ask AI  ────────────│──POST /chat─│                          │
│  Add Source ─────────│──POST /api──│  Provider (OpenRouter)   │
│  File Upload ────────│──POST /api──│  Embeddings (fastembed)  │
└──────────────────────┘             └────────────┬─────────────┘
                                                  │
                                          manifest.db
                                     SQLite + FTS5 + sqlite-vec
```

## Getting Started

### Prerequisites

- Python 3.12+, [uv](https://docs.astral.sh/uv/)
- Node.js 20+, [bun](https://bun.sh)
- [OpenRouter API key](https://openrouter.ai/keys) (free)

### Run locally

```bash
# Clone and setup
git clone https://github.com/samueldanso/evomind.git
cd evomind

# Seed the database with demo content + embeddings
uv run scripts/seed.py

# Start the backend
OPENROUTER_API_KEY=your-key uvicorn server:app --port 8765

# In another terminal — start the portal
cd portal && bun install && bun dev
```

Open [http://localhost:3000](http://localhost:3000)

### Add your own content

**From the UI:** Go to Add Source → paste text, drop a URL, or upload a PDF.

**From the CLI:**
```bash
uv run scripts/ingest.py --title "..." --slug "..." --tags "..." --summary "..." --html /path/to/file.html
uv run scripts/embed.py --incremental
```

### Run tests

```bash
uv run pytest                    # Python (150+ tests)
cd portal && bun test            # Portal tests
cd portal && bun run build       # Build check
```

## Deployment

| Service | Platform | Config |
|---------|----------|--------|
| Backend (FastAPI) | [Render](https://render.com) | `render.yaml` — Docker + persistent disk |
| Frontend (Next.js) | [Vercel](https://vercel.com) | `portal/vercel.json` — root dir `portal` |

### Environment Variables

**Render (backend):**
| Variable | Value |
|----------|-------|
| `OPENROUTER_API_KEY` | Your key (set as secret) |
| `EVO_STORE` | `/data` |
| `ALLOWED_ORIGIN` | Your Vercel URL |

**Vercel (frontend):**
| Variable | Value |
|----------|-------|
| `EVO_SERVER_URL` | Your Render URL |

## License

MIT
