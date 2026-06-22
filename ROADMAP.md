# Roadmap

Evo evolves from a personal local tool into an open-source agent-first learning platform.

> Read [VISION.md](./VISION.md) first. The vision is the destination — agents that research, write notes, and teach you, with a KB that compounds over time. The roadmap is the path.

**The intelligence substrate shipped in v0.2.0.** Provider abstraction, hybrid retrieval, embedding pipeline, eval harness, chat surface — all working. **The agent runtime lands in v0.3.0 (Phase D).** This is the first phase with executable agent behavior. Everything before it is substrate the agents write to and the surface they present through. Everything after it adds agents, tools, or memory capabilities. The runtime shape does not change after Phase D.

Retrieval already exists as a chat surface in v0.2.0. In v0.3.0 the same retrieval pipeline becomes a tool agents call. Chat stays — reframed as the secondary surface for querying what agents built. This is reframing, not rewriting.

---

## At a glance

| Phase | Name | Version | Status |
|---|---|---|---|
| A | Storage Foundation | v0.1.0 | ✅ Shipped |
| B | Control Surface | v0.1.0 | ✅ Shipped |
| C | Intelligence Substrate — provider abstraction, hybrid retrieval, embeddings, eval harness, chat surface | v0.2.0 | ✅ Shipped |
| **D** | **Agent Foundation — runtime, task contracts, tool interface, Research + Teaching agents** | **v0.3.0** | **Next** |
| E | Multi-source Ingest — PDF, URL, Markdown, codebases | v0.4.0 | Planned |
| F | Knowledge Quality — claims, contradiction detection, reconciliation | v0.5.0 | Planned |
| G | Agent Expansion — fact-checker, deepener, reconciler, async runtime, web_search tool | v0.6.0 | Planned |
| H | Portable — setup wizard, plugin SDK, Docker, docs | v0.7.0 | Planned |
| I | Open Source Release | v1.0.0 | Planned |
| J | Hosted Option | v2.0.0 | Conditional |

---

## Phase A — Storage Foundation ✅ (v0.1.0)

Persistent SQLite store with FTS5 manifest, ingest CLI, atomic upsert, 37 tests at 100% coverage.

This is the substrate. Agents in Phase D write their output here. The retrieval tool reads from here. The memory layer accumulates here. Storage is not the architecture — it is what the architecture sits on.

---

## Phase B — Control Surface ✅ (v0.1.0)

Next.js portal with card grid, FTS5 search, tag filters, artifact viewer, 33 vitest tests, CI gating.

This is the surface the user sees. Phase D makes it the surface through which agents are invoked. The portal is a window into what agents have built — not the product itself.

---

## Phase C — Intelligence Substrate ✅ (v0.2.0)

The substrate the agent layer runs on. Shipped four days ago. Everything in this phase becomes a tool or capability that agents call in Phase D.

**Shipped:**
- Provider abstraction — BedrockProvider (Claude Sonnet 4.6 + Cohere Embed v4 via boto3), env-swappable via `EVO_LLM_PROVIDER`
- Hybrid retrieval — vector + FTS5 + score-based merge (sequential, dedup by chunk_id)
- Embedding pipeline — batching, exponential backoff, Cohere Embed v4 at 1024 dims
- Migration-versioned SQLite — migration 002 (chunks, embeddings via sqlite-vec, claims stub — all in one file)
- `chunks` table with sentence-boundary chunker
- `embeddings` table via sqlite-vec
- Eval harness — 10-question retrieval quality gate, currently 10/10 on dogfood corpus
- `POST /api/chat` endpoint with grounded citations and hallucination guardrail
- `/chat` portal route — chat surface over the KB
- FastAPI `server.py` on port 8765 (repo root)
- 84 Python tests passing (2 skipped behind `RUN_LIVE_LLM=1`), CI green

**Reframing in v0.3.0 (no rewrite):**
- The retrieval pipeline becomes the implementation of the `retrieve` tool agents call
- The Provider abstraction becomes the implementation of the `generate` tool agents call
- The chat surface stays in place but is reframed as the secondary interface — query over what agents built
- The eval harness stays in place and gates that Phase D agent work does not regress retrieval quality

No code from Phase C is thrown away. Everything becomes substrate for the agent layer.

---

## Phase D — Agent Foundation (v0.3.0)

**The center of gravity lands here.**

### Goal

Introduce the agent runtime as the core architectural primitive. Ship:
- A typed task contract system
- A tool interface and tool router
- A tool allowlist per agent
- An agent execution loop
- An agent run log (full audit, replay-able)
- Two working agents: Research Agent and Teaching Agent
- The primary control surface: agent invocation UI

The `retrieve` and `generate` tools wrap the existing v0.2.0 retrieval pipeline and Provider abstraction. The `ingest` tool wraps existing ingest logic. No retrieval rebuild. The agents work with the production retrieval that already passes eval.

### Why the runtime lands here and not later

Without a runtime, every agent is a pipeline. Pipelines don't compose. They don't audit. They don't replay. They don't extend without restructuring. Introducing the runtime in Phase D means every subsequent phase — multi-source ingest, claims, fact-checker, deepener — plugs into the same pattern without changing core behavior. Phase D locks the shape.

### The runtime loop

```
Task dispatched (ResearchTask | TeachTask)
        ↓
Agent instantiated with task + tool allowlist
        ↓
Execution loop:
  agent calls tool(name, input)
  → tool router validates against allowlist
  → tool executes, returns typed output
  → tool call appended to run log
  → agent reasons over output
  → loop continues or exits
        ↓
Agent produces structured output
        ↓
Output ingested → artifacts table
Run persisted  → agent_runs table
```

### Task contracts

```python
@dataclass
class ResearchTask:
    task_type: Literal["research"]
    topic: str
    mode: Literal["concept", "tool", "company"]
    context: str | None = None

@dataclass
class TeachTask:
    task_type: Literal["teach"]
    topic: str
    artifact_slug: str | None = None
    mastery_context: str | None = None
```

### Tool interface

```python
class Tool(Protocol):
    name: str
    description: str
    def execute(self, input: dict) -> dict: ...
```

Phase D tools (each wraps existing v0.2.0 code, exposed under a Tool interface):

| Tool | What it does | Backing implementation | Used by |
|---|---|---|---|
| `retrieve` | hybrid vector + FTS5 + score-based merge | existing Phase C retrieval pipeline | Both agents |
| `generate` | LLM call via Provider | existing Phase C Provider abstraction (Bedrock default) | Both agents |
| `ingest` | write artifact to KB | existing ingest logic | Research Agent, Teaching Agent (checklist) |

`web_search` is not in Phase D. Stub returns empty results. Real implementation lands in Phase G.

### Agent run log

```sql
CREATE TABLE agent_runs (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  agent_type    TEXT NOT NULL,
  task_input    TEXT NOT NULL,
  status        TEXT NOT NULL DEFAULT 'running',
  output        TEXT,
  error         TEXT,
  tool_calls    TEXT NOT NULL DEFAULT '[]',
  cost_tokens   INTEGER NOT NULL DEFAULT 0,
  cost_usd      REAL NOT NULL DEFAULT 0.0,
  started_at    TEXT NOT NULL,
  finished_at   TEXT
);
```

Migration 003 in Phase D adds this table. Every tool call recorded in `tool_calls` as JSON array. Every run replayable from this record. Cost tracked from run zero — caps come in Phase G.

### The two agents

**Research Agent**
- Task: ResearchTask
- Allowlist: `retrieve`, `generate`, `ingest`
- Follows: research-wiki skill (embedded in system prompt)
- Flow: retrieve existing KB context → generate structured notes → ingest to KB
- Output: structured notes artifact in KB + run log entry

**Teaching Agent**
- Task: TeachTask
- Allowlist: `retrieve`, `generate`, `ingest`
- Follows: teach-me skill (embedded in system prompt)
- Flow: retrieve notes on topic → teach layer by layer via generate → quiz and verify → map connections → ingest mastery checklist
- Output: mastery checklist artifact in KB + run log entry

### Portal additions

**Agent invocation UI** (`/agent`) — the primary interface. Topic input, mode selector, context field. Submit dispatches an agent run. Status display shows running / complete / failed. Output links to the produced artifact.

**"Teach me this" button** — on every artifact in the portal. One click pre-fills the Teaching Agent form and navigates to `/agent`.

**Run history** — recent agent runs with status, cost, and output links.

**`/chat` route** — stays in place. Framing in nav and on-page copy updates: "Query what agents built." Not the primary surface anymore.

### Acceptance criteria

- [ ] Research Agent completes end-to-end: task in → artifact in KB + run log entry
- [ ] Teaching Agent completes end-to-end: task in → mastery checklist in KB + run log entry
- [ ] Every tool call recorded in `agent_runs.tool_calls`
- [ ] Tool allowlist enforced — unlisted tool call raises immediately
- [ ] Failed run records error + all tool calls made before failure
- [ ] Agent runs visible in portal with status and output links
- [ ] `retrieve`, `generate`, `ingest` tools wrap existing v0.2.0 implementations — no retrieval rebuild
- [ ] Migration 003 applies cleanly to fresh DB and existing v0.2.0 vault
- [ ] Phase C eval harness still passes 10/10 — no retrieval regression
- [ ] All new tests pass; existing 84+ Python tests still pass; CI green
- [ ] Samuel completes 3 Research runs + 3 Teaching runs on real topics before tagging v0.3.0
- [ ] CHANGELOG entry for v0.3.0 complete

### Out of scope

- Multi-source ingest → Phase E
- Claim extraction → Phase F
- `web_search` tool → Phase G (stub in Phase D returns empty)
- Async execution → Phase G
- Cost cap enforcement → Phase G (visibility only in Phase D)
- New retrieval work → not needed; v0.2.0 retrieval is production-ready

---

## Phase E — Multi-source Ingest (v0.4.0)

**Goal:** agents can ingest from PDFs, URLs, Markdown, and codebases — not just pre-processed HTML. The `ingest` tool is extended to accept any source type via the `IngestSource` plugin interface.

**In scope:**
- `IngestSource` protocol — `extract() → list[ExtractedArtifact]`
- PDF, URL, Markdown, codebase extractors
- Content normalization — all sources produce the same internal artifact shape
- Source type recorded in schema for filtered retrieval
- CLI flag dispatch — `--pdf`, `--url`, `--md`, `--repo`

**Release: v0.4.0**

---

## Phase F — Knowledge Quality (v0.5.0)

**Goal:** agents keep the KB honest as it grows. Claim extraction, deduplication, contradiction detection, supersession. The KB now self-corrects.

**In scope:**
- `claims`, `claim_sources`, `contradictions` tables (claims stub already exists from v0.2.0)
- Claim extraction — atomic claims with confidence from chunks
- Semantic deduplication — equivalent claims collapse
- Contradiction detection — pair-wise flagging
- Supersession — newer claim marks older one obsolete
- Reconciliation UI — review and resolve contradictions
- `claims` tool added to tool registry

**Release: v0.5.0**

---

## Phase G — Agent Expansion (v0.6.0)

**Goal:** expand the agent layer and harden the runtime. Three new agents. Async execution. Cost caps. Full tracing. `web_search` tool — the Research Agent finally has live web access.

**In scope:**
- `web_search` tool (Brave / Tavily / Exa — Hermes resolves)
- Research Agent upgraded — real web search replaces stub
- Async orchestration runtime
- Cost cap enforcement per agent run
- OpenTelemetry tracing
- Fact-Checker agent
- Deepener agent
- Reconciler agent
- Slash commands in chat — `/research`, `/teach`, `/factcheck`, `/deepen`

**Release: v0.6.0**

---

## Phase H — Portable (v0.7.0)

First-run setup wizard, configurable store backends, Docker compose, Plugin SDK, single-user auth, documentation site. Anyone can install and run in 5 minutes.

**Release: v0.7.0**

---

## Phase I — Open Source Release (v1.0.0)

Public, polished, community-ready. Samuel has used it daily for 90 consecutive days. 30+ topics researched. 10+ agent runs in the dogfood vault. One external install test. All Phase A–H acceptance criteria pass.

**Release: v1.0.0**

---

## Phase J — Hosted Option (v2.0.0, conditional)

Only if v1.0 reaches 1,000+ stars and 100+ active self-hosters. LLM Gateway, sandboxed agent execution, multi-tenant isolation, usage-based billing. Not committing to scope or dates.

---

## Working principles

1. **Agent-first.** Every new capability is an agent or a tool. Not a pipeline step.
2. **Chat is secondary.** The primary interface is agent invocation. Chat is the retrieval surface.
3. **Personal-first.** Samuel uses every phase before it ships publicly.
4. **Tagged releases only.** Every merge to main gets a CHANGELOG entry.
5. **Tests gate every release.** pytest + vitest + portal build in CI.
6. **Forward-only migrations.** No breaking schema changes without migration scripts.
7. **Local-first forever.** Self-host path stays first-class even in the hosted version.
8. **Justification required.** Every capability is tied to the user pressure that demanded it.
9. **Cost-bounded by default.** Every agent run records token + USD cost from run zero. Caps land in Phase G.
10. **No rebuild of shipped substrate.** Phase D wraps Phase C code in Tool interfaces. No retrieval rebuild, no Provider rewrite.

---

## Open questions before each phase

**Before Phase D:**
- Agent loop — custom Python loop (recommended) or thin wrapper over existing primitive (smolagents, LangGraph)?
- Teaching session turns — portal polling or WebSocket?
- Auto-chain Research → Teaching — default on (recommended) or opt-in?

**Before Phase E:**
- HTML extraction — trafilatura or readability-lxml?
- PDF extraction — pypdf or pdfplumber?

**Before Phase F:**
- Claim extraction prompt schema
- Contradiction detection — pair-wise or graph-based?
- Human resolution flow — accept / reject / edit?

**Before Phase G:**
- Async runtime — Celery/Redis or native Python async?
- Web search provider — Brave, Tavily, or Exa?
- Cost cap — per-run, per-day, or both?
