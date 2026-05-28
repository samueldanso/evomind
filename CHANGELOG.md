# Changelog

All notable changes to EvoResearch are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/samueldanso/evo-research/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/samueldanso/evo-research/releases/tag/v0.1.0
