# Roadmap

EvoResearch is evolving from a personal local tool into an open-source system others can run. This roadmap tracks that arc.

## Phase A — Brain ✅
Persistent store + SQLite FTS5 manifest + ingest CLI.

## Phase B — Portal ✅
Local Next.js web app: card grid, full-text search, tag filters, artifact viewer.

## Phase C — Intelligence Layer
RAG over the corpus via `sqlite-vec`.
- Vector embeddings stored alongside artifact metadata
- "Ask your research" chat interface
- Evo queries manifest + vectors before generating new research

## Phase D — Multi-User & Open Source
Make the system runnable by anyone, not just on Samuel's Mac.
- Remove hardcoded iCloud vault path — first-run setup wizard
- Configurable store backend (local fs, S3, custom path)
- Docker-compose for portal + optional embedding worker
- Auth layer (single-user token to start)
- Public docs site
- Community ingest plugins (browser extension, CLI, API)

## Phase E — Hosted Option
Optional cloud-hosted version for users who don't want to self-host.
- Managed vault storage
- Shared corpus / team workspaces
- Usage-based billing

---

> Phases C–E are directional. Dates and scope will be refined as Phase B stabilises and open-source release approaches.
