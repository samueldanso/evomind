# Roadmap

EvoResearch is evolving from a personal local tool into an open-source learning and research partner. This roadmap tracks that arc, with version cuts and release markers.

> Read [VISION.md](./VISION.md) first. The vision is the destination — a system that builds and protects your understanding of a domain over time. The roadmap is the path.

The phases below are ordered to deliver that value early and protect it as it grows. Phase C ships chat over your existing sources. Phase D opens the system to the source types learners actually use. Phase E adds the quality mechanisms (reconciliation, contradiction detection) that keep understanding honest as it grows. Phase F adds research agents that extend what you know.

## At a glance

| Phase | Name | Version | Status |
|---|---|---|---|
| A | Brain — persistent store + ingest CLI + FTS5 | v0.1.0 | ✅ Shipped |
| B | Portal — local web app, browse + search + view | v0.1.0 | ✅ Shipped |
| **C** | **Intelligence Layer — chunks, embeddings, RAG chat, claim stub** | **v0.2.0** | **Next** |
| D | Multi-source ingest — PDF, URL, Markdown, codebases | v0.3.0 | Planned |
| E | Reconciliation — claim extraction, contradiction detection, KB rewrite | v0.4.0 | Planned |
| F | Agentic research — sub-agent spawning for fact-check + deepen | v0.5.0 | Planned |
| G | Portable — config wizard, plugin SDK, deploy docs | v0.6.0 | Planned |
| H | Open source release — public docs, community ingest plugins | **v1.0.0** | Planned |
| I | Hosted option — optional managed cloud version | v2.0.0 | Directional |

Versions follow [semver](https://semver.org/). Each phase ships a tagged release with a complete CHANGELOG entry.

---

## Phase A — Brain ✅ (shipped v0.1.0)

**Status:** complete and tagged.

Persistent SQLite store with FTS5 manifest, ingest CLI (`scripts/ingest.py`), `EVO_RESEARCH_STORE` env override, atomic upsert, 37 tests at 100% coverage.

---

## Phase B — Portal ✅ (shipped v0.1.0)

**Status:** complete and tagged.

Next.js 16 + React 19 portal with card grid, full-text search via FTS5 BM25, tag filters, artifact viewer with CSP + path confinement, 33 vitest tests, CI gating on every push.

---

## Phase C — Intelligence Layer (v0.2.0)

**Goal:** make every artifact queryable via natural-language chat with cited retrieval, and lay the schema foundation for claim-level reasoning that lands in Phase E.

**In scope:**

- Add `chunks` table — sub-artifact text spans with deterministic chunking from HTML
- Add `embeddings` table via `sqlite-vec` — vector search alongside FTS5
- Add `claims` table as a stub — empty schema in place, populated in Phase E
- Embedding pipeline — background script that ingests new artifacts and chunks them
- Chat API endpoint — `POST /api/chat` with hybrid retrieval (vector + FTS5) and grounded response with citations
- Chat UI — minimal sidebar chat interface in the portal, retrieves and displays citations
- Pluggable LLM provider — start with Anthropic Claude via API key in `.env.local`
- Embedding model decision locked (recommend: `text-embedding-3-small` for cost; nomic-embed-text for full-local optionality later)

**Out of scope (deferred):**

- Multi-source ingest (still HTML only — Phase D)
- Claim extraction (table exists but no extraction logic — Phase E)
- Agent spawning (Phase F)
- Contradiction surfacing UI (Phase E)

**Acceptance criteria:**

- New chunks generated for all existing artifacts via one-shot reindex script
- `POST /api/chat?q=...` returns an answer grounded in chunks with `artifact_id`-anchored citations
- Chat UI shows answer + clickable citations that open the source artifact at the relevant chunk
- Hybrid retrieval improves answer quality vs FTS5-only baseline on a 20-question eval set Samuel writes
- `claims` table schema exists, migration tested, no extraction logic yet
- 20+ new pytest tests cover chunking, embedding, retrieval; 15+ new vitest tests cover chat route
- Vault remains the canonical store — embeddings live in `manifest.db` alongside the artifacts table
- Local-only — no telemetry, no remote logging

**Release: v0.2.0** — CHANGELOG entry: *"Phase C: chat over your research with grounded citations."*

**Risks to flag:**

- Embedding cost at scale — quantify per 100 artifacts before opening to others
- Chunk size vs retrieval quality — needs eval set
- Lock-in to one LLM provider — abstract through a `Provider` interface even at v0.2.0

---

## Phase D — Multi-source ingest (v0.3.0)

**Goal:** expand what can flow into the system beyond Hermes-generated HTML. This unlocks the daily-use case for any learner who isn't already feeding it HTML.

**In scope:**

- Define `IngestSource` interface — every source type implements `extract() → list[ExtractedArtifact]`
- PDF ingest — lecture notes, papers, textbooks (use `pdf` skill / pypdf2 / pdfplumber)
- URL ingest — paste a URL, system fetches and extracts main content
- Markdown ingest — Obsidian notes, README files
- Codebase ingest — point at a repo, extract README + key source comments + structure
- CLI flag dispatch — `--pdf path`, `--url https://...`, `--md path`, `--repo path`
- Content extraction is a single normalisation step — all sources produce the same internal artifact shape

**Out of scope (deferred):**

- Browser extension for one-click ingest (Phase G)
- Watch folders / auto-ingest (Phase G)
- Audio / video transcripts (post-v1)

**Acceptance criteria:**

- All four source types ingest cleanly with at least one real example per type
- Chunks and embeddings auto-generated for new source types (Phase C pipeline reused)
- Source type is recorded in schema (`artifact_source_type`) for future filtering
- 15+ new pytest tests cover each extractor
- Existing HTML pipeline still works unchanged — no regressions

**Release: v0.3.0** — CHANGELOG entry: *"Phase D: ingest from PDFs, URLs, Markdown, and codebases."*

---

## Phase E — Reconciliation (v0.4.0)

**Goal:** keep your understanding honest as it grows. Turn the corpus from a static archive into a knowledge base that surfaces contradictions across sources, supersedes stale claims, and lets you resolve conflicts as new sources arrive. This is the quality mechanism that makes the learning loop trustworthy — without it, the KB just gets bigger; with it, the KB gets *truer* over time.

**In scope:**

- Claim extraction — LLM extracts atomic claims from each chunk with `(claim_text, confidence, source_chunk_id)` tuples
- Claim deduplication — semantic dedup to collapse equivalent claims across sources
- Contradiction detection — pair-wise claim comparison flags conflicting claims with `contradiction` table entries
- Supersession — when a newer claim contradicts an older one, the system marks the older one `superseded_by`
- Reconciliation UI — portal page showing surfaced contradictions, with one-click "review and decide"
- KB rewrite mechanism — when Samuel resolves a contradiction, the canonical answer updates

**Out of scope (deferred):**

- Multi-hop reasoning (Phase F via agents)
- External fact-checking via web search (Phase F via agents)
- Auto-resolution without human review (post-v1, requires trust we don't have yet)

**Acceptance criteria:**

- Ingesting two artifacts with conflicting claims about the same topic surfaces the contradiction in the UI within one indexing pass
- Resolving a contradiction marks the losing claim `superseded_by` and updates retrieval to prefer the canonical answer
- 25+ new pytest tests cover extraction, dedup, contradiction detection, supersession
- Eval set: 10 hand-crafted artifact pairs with known contradictions, system catches at least 8

**Release: v0.4.0** — CHANGELOG entry: *"Phase E: claim-level reconciliation. Your KB now detects and resolves contradictions."*

**Risks to flag:**

- LLM cost of claim extraction at scale — needs batching and incremental processing
- False-positive contradictions — calibration matters more than recall
- Schema mutation cost — `claims` and `contradictions` tables need migration discipline

---

## Phase F — Agentic research (v0.5.0)

**Goal:** sub-agents that extend what you're learning — by going deeper on a topic, verifying against primary sources, or gathering more evidence around a contradiction. This is what turns EvoResearch from a system that holds your understanding into one that *grows it with you*.

**In scope:**

- Agent runtime — Python orchestration layer that spawns sub-agents with scoped tasks
- Built-in agents:
  - **Fact-Checker** — given a claim, web-search for primary sources, return verdict
  - **Deepener** — given a topic, generate new research and ingest it as new artifacts
  - **Reconciler** — given a contradiction, gather more evidence to inform resolution
- Agent runs persisted in `agent_runs` table for audit and replay
- Agent invocation from chat UI — `/factcheck`, `/deepen`, `/reconcile` slash commands
- Agent results ingested as new artifacts, closing the loop

**Out of scope (deferred):**

- Multi-agent parallel orchestration (single agent per task in v0.5.0)
- Agent skill marketplace (post-v1)
- Autonomous background agents (v1.x — opt-in only)

**Acceptance criteria:**

- Spawning a Fact-Checker on a known-wrong claim produces a contradiction entry within 60 seconds
- Spawning a Deepener on a topic produces 1+ new artifact ingested into the KB
- Every agent run is replayable from `agent_runs` log
- Cost cap per agent run is configurable and enforced
- 20+ new pytest tests cover agent orchestration

**Release: v0.5.0** — CHANGELOG entry: *"Phase F: spawn fact-checking and research agents from chat."*

---

## Phase G — Portable (v0.6.0)

**Goal:** remove every assumption that "this only runs on Samuel's Mac." Prepare for open source release.

**In scope:**

- First-run setup wizard — no more hardcoded iCloud path; user picks vault location
- Configurable store backends — local fs (default), S3-compatible (optional)
- `.env` schema and validation — required keys checked on startup
- Docker compose — portal + Python services run in containers
- Documentation site — install, config, ingest sources, chat, agents, troubleshooting
- Plugin SDK — interface for community ingest source plugins
- Single-user auth token — protects the portal when not on localhost
- Telemetry: **opt-in only**, off by default, fully documented what's sent

**Out of scope (deferred):**

- Multi-user / team workspaces (post-v1)
- SSO (post-v1)
- Cloud-hosted version (Phase I)

**Acceptance criteria:**

- A fresh checkout on Linux runs `docker compose up` and reaches a working portal in under 5 minutes
- Setup wizard handles vault path on macOS, Linux, and Windows
- Docs site builds and deploys (Vercel or similar) with full coverage of install + first ingest
- No hardcoded paths anywhere in the codebase (lint rule enforces this)
- Plugin SDK ships with one reference plugin (browser extension or Notion ingest)

**Release: v0.6.0** — CHANGELOG entry: *"Phase G: portable. Anyone can install and run EvoResearch."*

---

## Phase H — Open source release (v1.0.0)

**Goal:** public, polished, community-ready.

**In scope:**

- Public GitHub release with full README, demo gif, install one-liner
- Public docs site
- Launch posts: HN, X, builder Discord communities, dev.to
- Issue templates, contribution guide, code of conduct
- Tagged v1.0.0 — semver promise: no breaking changes within v1.x without deprecation warning
- Reference deployment example (self-host on a $5 VPS)
- At least 5 community ingest plugins available at launch

**Acceptance criteria for v1.0.0:**

- VISION.md and ROADMAP.md polished for public reading
- Samuel has used it daily for 90 consecutive days
- 30+ test artifacts, 5+ surfaced contradictions, 3+ agent runs in the dogfood vault
- One real public install test (someone outside Samuel's circle, fresh machine, follows docs)
- All Phase A–G acceptance criteria still pass
- Tagged v1.0.0, GitHub release with binary attachments where relevant

**Release: v1.0.0** — CHANGELOG entry: *"v1.0: EvoResearch is public."*

---

## Phase I — Hosted option (v2.0.0, directional)

**Goal:** optional managed cloud version for users who don't want to self-host.

This phase is conditional. We only build it if:

- v1.0 open source demonstrates at least 1,000 stars and 100+ active self-hosters
- There is genuine demand from non-technical users who cannot self-host
- The economics work (margin on managed embeddings + LLM cost)

**Possible scope:**

- Managed vault storage
- Shared corpus / small-team workspaces
- Usage-based billing
- Optional shared agents / community claim feeds

**Not committing to dates or scope here.** This phase exists in the roadmap to signal direction; it does not commit engineering.

---

## Working principles across all phases

1. **Personal-first.** Samuel uses every phase before it ships publicly.
2. **Tagged releases only.** Nothing merges to `main` that doesn't go into a CHANGELOG entry.
3. **Tests gate every release.** pytest + vitest + portal build must pass in CI.
4. **No breaking schema changes without migration scripts.** SQLite migrations are versioned from v0.2.0 onwards.
5. **Local-first forever.** Even the hosted option must keep the self-host path first-class.
6. **Understanding deeper, not files bigger.** When in doubt, see VISION.md decision principle.

---

## Open questions to resolve before each phase starts

These are Hermes (PM) questions, not Claude Code questions. They should be resolved in a planning doc (`tasks/plan-phase-X.md`) before any implementation begins.

**Before Phase C:**

- Embedding model — Anthropic Voyage, OpenAI, or local nomic?
- LLM provider abstraction — what's the minimum viable Provider interface?
- Chunk strategy — fixed-size, semantic, or document-structure-aware?

**Before Phase D:**

- HTML extraction library — Mozilla Readability port, trafilatura, or custom?
- PDF extraction — pypdf, pdfplumber, or pdf-skill's existing tooling?

**Before Phase E:**

- Claim extraction prompt schema — what does the model return?
- Contradiction detection — pair-wise comparison only, or graph-based?
- How does Samuel resolve a contradiction — accept/reject/edit?

**Before Phase F:**

- Agent orchestration framework — custom, or use an existing one (LangGraph, smolagents)?
- Cost cap mechanism — per-run, per-day, both?
- Tool surface for agents — web search via which provider?

**Before Phase G:**

- Docker base image policy
- Docs site framework (Mintlify, Nextra, or custom Next.js)
- Plugin SDK shape — Python module, HTTP webhook, or both?
