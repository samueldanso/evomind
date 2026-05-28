# EvoResearch

A persistent, corpus-aware research knowledge system. Every research artifact is saved permanently to an iCloud vault with full-text search, and browsable via a local web portal.

## Stack

- **Brain:** Python 3.12 + SQLite FTS5 — ingest CLI, search, manifest
- **Portal:** Next.js 16, Tailwind v4, shadcn/ui — browse, search, read

## Usage

```bash
# Save a research artifact
uv run scripts/ingest.py \
  --title "..." --slug "my-topic" \
  --tags "ai,agents" --topics "llm,tooling" \
  --summary "..." --html /path/to/file.html

# Search the corpus
uv run scripts/ingest.py --search "claude agents"

# List all artifacts
uv run scripts/ingest.py --list

# Run the portal
cd portal && bun dev
```

## Vault

Artifacts are stored at:
```
~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Samuel's Vault/HomeOS/Knowledge/Research/
├── manifest.db    # SQLite + FTS5 index
├── html/          # Permanent HTML pages
└── summaries/     # Companion .md notes
```

Override with `EVO_RESEARCH_STORE=/path/to/store`.

## Dev

```bash
uv run pytest          # Python tests (run before every commit)
cd portal && bun run build   # Portal build
```
