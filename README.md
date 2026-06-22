# Evo

> Your personal knowledge base where agents research, write, and teach — understanding compounds with every session.

Evo is an agent-first learning platform. You direct agents to go deep on a topic. They research it, write structured notes into your knowledge base, then teach you from those notes. Every session compounds into the next. Chat is how you retrieve what the agents built.

## Architecture

Evo follows the *Agent = LLM + Harness* framework (NVIDIA GTC 2026). The LLM is the reasoning core; the harness is everything around it tåhat turns reasoning into compounding action — context assembly, the observe-reason-act loop, persistent memory, tools, skills, orchestration, and audit.

```
                       ┌─────────────────────────────┐
                       │  LLM (Bedrock)           ✅ │
                       │  Claude Sonnet 4.6          │
                       │  core/llm/bedrock.py        │
                       └──────────────┬──────────────┘
                                      │
  ┌───────────────────┐   ┌───────────▼───────────┐   ┌───────────────────┐
  │ PROMPT         ✅ │◄─►│     Inner Loop     ✅ │◄─►│ TOOLS & SKILLS    │
  │ core/prompts/  ✅ │   │  ┌─────────────────┐  │   │ core/tools/    ✅ │
  │ research-wiki     │   │  │ Context         │  │   │  retrieve      ✅ │
  │ teach-me          │   │  │ Observe         │  │   │  generate      ✅ │
  └───────────────────┘   │  │ Reason          │  │   │  ingest        ✅ │
                          │  │ Act             │  │   │  web_search    🔵 │
  ┌───────────────────┐   │  └─────────────────┘  │   └───────────────────┘
  │ ORCHESTRATION  ✅ │   │  core/runtime/     ✅ │
  │ Agent dispatcher  │   └───────────┬───────────┘   ┌───────────────────┐
  │ Research→Teaching │               │               │ SECURITY & AUDIT  │
  │ auto-chain        │               │               │ Tool allowlist ✅ │
  └───────────────────┘               │               │ agent_runs log ✅ │
                                      ▼               │ cost tracking  ✅ │
                       ┌─────────────────────────────┐└───────────────────┘
                       │ MEMORY                      │
                       │  artifacts             ✅   │
                       │  chunks                ✅   │
                       │  embeddings            ✅   │
                       │  claims (stub)         ✅   │
                       │  agent_runs            ✅   │
                       │  mastery checklists    ✅   │
                       └─────────────────────────────┘
```

**Status:** ✅ shipped through v0.3.0 (agent foundation) · 🔵 later phases

Phase D wraps the existing v0.2.0 retrieval pipeline and Provider abstraction under Tool interfaces. No retrieval rebuild, no provider rewrite.

## Quick start

```bash
# Ingest a research artifact
uv run scripts/ingest.py \
  --title "..." --slug "my-topic" \
  --tags "ai,agents" --topics "llm,tooling" \
  --summary "..." --html /path/to/file.html

# Embed chunks for retrieval
uv run scripts/embed.py --incremental

# Run an agent
uv run scripts/agent.py --task research --topic "KV Cache" --mode concept
uv run scripts/agent.py --task teach --topic "KV Cache"

# Start the server
uvicorn server:app --port 8765

# Run the portal
cd portal && bun dev

# Run tests
uv run pytest
cd portal && bun test && bun run build
```

## Vault

Artifacts are stored at:
```
~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Samuel's Vault/SamuelOS/Knowledge/
├── manifest.db    # SQLite + FTS5 + sqlite-vec
├── html/          # Permanent HTML pages
└── summaries/     # Companion .md notes
```

Override with `EVO_STORE=/path/to/store`.

## Stack

- **Brain:** Python 3.12+, uv, FastAPI, SQLite (FTS5 + sqlite-vec), boto3 (Bedrock)
- **Portal:** Next.js 16, React 19, Tailwind v4, shadcn/ui, Biome, bun
- **LLM:** Bedrock — Claude Sonnet 4.6 (chat) + Cohere Embed v4 (embeddings, 1024 dims)

## Project structure

```
core/                     # harness — platform primitives
├── llm/                  #   LLM provider layer
│   ├── __init__.py       #   re-exports
│   └── bedrock.py        #   BedrockProvider (Claude + Cohere Embed)
├── memory/               #   KB read/write + retrieval
│   ├── __init__.py       #   re-exports
│   ├── db.py             #   shared DB helpers
│   ├── retrieval.py      #   hybrid FTS5 + vec search
│   └── chunker.py        #   sentence-boundary splitter
├── agents/               #   agent definitions (research, teaching)
├── runtime/              #   execution loop, dispatcher, contracts
├── tools/                #   tool interface (retrieve, generate, ingest)
├── prompts/              #   skill instruction templates
└── governance/           #   audit + allowlist

server/                   # FastAPI package — /chat, /api/agent
├── __init__.py           #   app factory, lifespan, CORS
└── routes/               #   route modules (chat, agent)
scripts/                  # CLI tools (ingest, embed, eval, migrate, agent)
tests/                    # pytest suite (137 passing)
portal/                   # Next.js frontend (41 tests)
```

## Read more

- [VISION.md](./VISION.md) — product vision, harness component map, agent descriptions
- [ROADMAP.md](./ROADMAP.md) — phase sequence with acceptance criteria
- [CAPABILITIES.md](./CAPABILITIES.md) — platform capability map with phase-by-phase justification
- [CHANGELOG.md](./CHANGELOG.md) — what's actually shipped
