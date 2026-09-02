# Capabilities

> What NeuroWiKi is, in platform terms. Agent runtime first. Tools second. Retrieval third. Storage at the foundation.
>
> Read [VISION.md](./VISION.md) for the product framing. Read [ROADMAP.md](./ROADMAP.md) for phase timing.

## How to read this

Agent runtime first. Tools that agents call second. Retrieval as a tool third. Storage at the foundation. The ordering is the thesis.

Capabilities are ordered by architectural priority — agent runtime at the top, storage at the bottom. The Justification column is the discipline: every capability is tied to the user pressure that demanded it. No justification = warning sign.

---

## Agent Runtime & Orchestration *(Harness: Observe-Reason-Act + Orchestration)*

| Capability | Phase | Status | Justification |
|---|---|---|---|
| Agent execution loop — dispatch, tool calls, output, run log | D | planned | The runtime is the core primitive. Everything else plugs into it. |
| Typed task contracts — ResearchTask, TeachTask | D | planned | Agents need typed input to be composable, testable, and auditable |
| Tool interface — Protocol with typed input/output | D | planned | Tools are agent capabilities. The interface makes them swappable without changing agents. |
| Tool allowlist per agent | D | planned | Bounded tools are a safety and composability property from day one |
| `agent_runs` table — full tool call log, status, cost | D | planned | Non-determinism in agents requires audit. Run log is the foundation. |
| Cost tracking per run (tokens + USD) | D | planned | Visibility from run zero. Enforcement comes in Phase G. |
| Async orchestration runtime | G | planned | Earn this when Phase G agents run autonomously and blocking becomes a real problem |
| Per-run cost cap enforcement | G | planned | Caps needed when agents run without explicit user invocation |
| OpenTelemetry tracing | G | planned | Multi-step agent failure is undebuggable from logs alone; earn when Phase G runs are habitual |
| Parallel multi-agent execution | G | planned | Single agent per task first. Parallelism after the pattern is proven. |
| Replay from agent_runs log | G | planned | Meaningful once Phase G agents run autonomously |

---

## Agent Layer *(Harness: instantiated agents)*

| Capability | Phase | Status | Justification |
|---|---|---|---|
| Research Agent — researches topic, writes notes to KB | D | planned | First agent. Establishes the runtime pattern. Core loop requires it. |
| Teaching Agent — teaches from notes, writes mastery checklist | D | planned | Second agent. Core loop requires both research and teaching. |
| Fact-Checker Agent — verifies claim against primary sources | G | planned | Requires `web_search` tool and full async runtime |
| Deepener Agent — finds adjacent topics, spawns Research + Teaching runs | G | planned | Requires cost caps — runs autonomously without explicit user invocation |
| Reconciler Agent — gathers evidence to resolve contradictions | G | planned | Requires contradiction detection from Phase F to have claims to act on |

---

## Tool Layer *(Harness: Tools & Skills)*

| Capability | Phase | Status | Justification |
|---|---|---|---|
| `retrieve` — hybrid retrieval (vector + FTS5 + score-based merge) | D | wraps ✅ v0.2.0 | Existing v0.2.0 retrieval exposed under Tool interface. No rebuild. |
| `generate` — LLM text generation via Provider | D | wraps ✅ v0.2.0 | Existing v0.2.0 Provider abstraction exposed under Tool interface. No rebuild. |
| `ingest` — write artifact to KB | D | wraps ✅ v0.1.0 | Existing ingest logic exposed under Tool interface. No rebuild. |
| `web_search` — live web search (stub in D, real in G) | G | planned | Stub in Phase D returns empty. Real implementation requires Fact-Checker + async runtime. |
| `claims` — read/write claim-level knowledge | F | planned | Requires claims table and extraction logic from Phase F |

---

## Retrieval & Intelligence

| Capability | Phase | Status | Justification |
|---|---|---|---|
| FTS5 full-text search over artifacts | A/B | ✅ v0.1.0 | Minimum viable search for portal and retrieval tool |
| Path-confined HTML serving with CSP | B | ✅ v0.1.0 | Untrusted research HTML in sandboxed iframe |
| Provider abstraction across LLM vendors | C | ✅ v0.2.0 | First LLM integration required avoiding lock-in from day one. Currently: Bedrock-only (Claude Sonnet 4.6 + Cohere Embed v4 via boto3). |
| Hybrid retrieval — vector + FTS5 + score-based merge | C | ✅ v0.2.0 | Eval showed neither vector nor FTS alone covered the question space |
| `chunks` table — sentence-boundary text spans | C | ✅ v0.2.0 | Sub-artifact granularity required for retrieval quality |
| `embeddings` table via sqlite-vec | C | ✅ v0.2.0 | Vector search requires embeddings |
| Embedding pipeline — batching + exponential backoff | C | ✅ v0.2.0 | API-bound work needs resilience to rate limits, even at corpus scale of 7 |
| Eval harness with retrieval quality gate | C | ✅ v0.2.0 | 10-question gate, currently 10/10. Gates Phase D agents do not regress retrieval. |
| Migration-versioned SQLite schema | C | ✅ v0.2.0 | Forward-only discipline from first schema change. Migration 002 shipped (chunks + embeddings + claims stub). |
| `claims` table stub | C | ✅ v0.2.0 | Cheap to land schema before Phase F activates it; retrofit cost is high |
| `IngestSource` plugin interface | E | planned | Multi-source ingest requires a normalized contract |
| Source-typed retrieval | E | planned | Filtering by source type requires source type in schema |
| Semantic chunking (heading-aware) | post-E | considered | Only if fixed-size chunking shows real quality loss on eval growth |

---

## Knowledge Quality & Reconciliation

| Capability | Phase | Status | Justification |
|---|---|---|---|
| `claims` table stub | C | ✅ v0.2.0 | Schema landed early; activation in Phase F |
| Claim extraction with confidence | F | planned | Reconciliation requires atomic claims; chunk granularity is insufficient |
| Semantic claim deduplication | F | planned | Same fact in 3 sources should collapse, not triple-count |
| Pair-wise contradiction detection | F | planned | Surfacing contradictions is the central "kept honest" mechanism |
| Supersession infrastructure | F | planned | KB evolves; older claims must be markable as obsolete, not deleted |
| Claim-source provenance graph | F | planned | Every claim traces back to the chunks it was extracted from |
| Reconciliation UI | F | planned | Human review surface for flagged contradictions |
| Confidence calibration over time | post-v1 | considered | Meaningful only once claim corpus is large enough to evaluate |

---

## Memory Layer *(Harness: Memory)*

| Capability | Phase | Status | Justification |
|---|---|---|---|
| Artifact store — research agent writes, portal reads | A | ✅ v0.1.0 | Storage foundation |
| Mastery checklists — teaching agent output persisted | D | planned | Teaching session value evaporates without persistence |
| Agent run log — every run replayable | D | planned | Audit and replay require the log from the first run |
| Concept connections — mapped at end of teaching sessions | D | planned | Connections are part of mastery checklist output |
| Claim-level memory — atomic facts with provenance | F | planned | Chunk-level memory insufficient for contradiction detection |

---

## Control Surface

| Capability | Phase | Status | Justification |
|---|---|---|---|
| Browse portal — artifact grid, search, viewer | B | ✅ v0.1.0 | Minimum viable surface to see what's in the KB |
| Chat retrieval surface (`/chat`) | C | ✅ v0.2.0 | Originally shipped as primary surface in v0.2.0; reframed in v0.3.0 as secondary — query what agents built |
| Agent invocation UI (`/agent`) | D | planned | Primary interface in v0.3.0. Agents are how you direct the system. Ships with the runtime. |
| "Teach me this" button on artifacts | D | planned | One-click path from KB artifact to teaching session |
| Agent run history | D | planned | Users need to see what agents have done and what they produced |
| Slash commands — `/research`, `/teach`, `/factcheck` | G | planned | Conversational agent invocation; earn when async runtime supports it |

---

## Storage & Data Plane

| Capability | Phase | Status | Justification |
|---|---|---|---|
| Single-file SQLite vault (FTS5 + sqlite-vec) | A → C | ✅ shipped | Local-first, single-user; postgres + qdrant is overkill until Phase J |
| Path confinement on all FS access | B | ✅ v0.1.0 | Untrusted artifact content must not escape the vault |
| Atomic upsert with conflict resolution | A | ✅ v0.1.0 | Re-ingest must update, never duplicate |
| Cascade-deleted child rows | C | ✅ v0.2.0 | Archive an artifact → chunks + embeddings clean up automatically |
| Knowledge graph (Neo4j or equivalent) | post-v1 | not committed | Vector + FTS + claims may be sufficient; let corpus growth decide |

---

## Portability & Distribution

| Capability | Phase | Status | Justification |
|---|---|---|---|
| Env-overridable vault path | A | ✅ v0.1.0 | First step away from hardcoded macOS iCloud path |
| Validated env at startup (boto3 client creation fails loud) | C | ✅ v0.2.0 | Never silent fallback on missing credentials |
| First-run setup wizard | H | planned | Strangers can't be expected to read docs before installing |
| Configurable store backend (local, S3) | H | planned | Self-hosters on Linux need non-iCloud paths |
| Docker compose deployment | H | planned | The 5-minute-install bar |
| Plugin SDK (community ingest sources) | H | planned | Community contribution surface |
| Single-user auth token | H | planned | Portal bound to non-localhost needs auth |
| Hosted multi-tenant deployment | J | conditional | Only if open source demonstrates demand |

---

## Multi-Tenant Platform Layers (Phase J, conditional)

| Capability | Phase | Status | Justification |
|---|---|---|---|
| LLM Gateway — rate limiting, fallback routing, semantic caching | J | conditional | Multi-tenant cost control demands a gateway |
| Sandboxed agent execution (E2B / Firecracker) | J | conditional | One user's agent must not affect another's environment |
| Per-tenant cost attribution | J | conditional | Billing and quota enforcement |
| Audit log export | J | conditional | Compliance signal for team adoption |
| Provider key rotation / vault | J | conditional | Keys-as-a-service for hosted users |

---

## What this doc proves

Agent runtime first. Tools that agents call second. Retrieval as a tool third. Chat as the retrieval surface fourth. Storage at the foundation.

The ordering is the thesis. Anyone can list platform buzzwords. Few can show the trail of decisions — with justification — that landed an agent platform on top of a product people actually use, phase by phase, user pressure documented throughout. The Justification column is what separates engineering from resume-writing. This doc is the index of that trail.

## How this doc stays honest

- Every new capability lands in this table when its phase ships
- Justification column is mandatory — no justification is a warning sign
- Capabilities explicitly not built are recorded — saying no is also a signal
- Updated in the same PR that delivers the capability. No backfilling.
