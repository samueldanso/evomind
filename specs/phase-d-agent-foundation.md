# Phase D — Agent Foundation

> Target release: **v0.3.0**. Hermes plans, Claude Code executes.

## Objective

Introduce the agent runtime as the core architectural primitive of EvoResearch. This is the phase where the product becomes an agent platform.

Ship:
- A typed task contract system
- A tool interface and tool router with allowlist enforcement
- An agent execution loop
- A persistent agent run log (full audit, cost tracking)
- Two working agents: Research Agent and Teaching Agent
- The primary control surface: agent invocation UI

The `retrieve`, `generate`, and `ingest` tools wrap the existing v0.2.0 code under the new Tool interface. **No retrieval rebuild. No Provider rewrite.** The agents work with the production retrieval pipeline that already passes eval.

**The primary user interface after Phase D is `/agent` — not `/chat`. Chat stays in place from v0.2.0, reframed as the secondary retrieval surface over what agents built.**

---

## What is not in scope

- New retrieval work → not needed; v0.2.0 retrieval is production-ready and eval-passing
- Multi-source ingest → Phase E
- Claim extraction → Phase F (`claims` stub already shipped in v0.2.0)
- `web_search` tool → Phase G (stub in Phase D returns empty)
- Async execution → Phase G
- Cost cap enforcement → Phase G (cost is tracked in Phase D, not capped)
- Streaming responses in agent UI → Phase D.1 patch
- Provider rewrite → not needed; Bedrock-default Provider abstraction shipped in v0.2.0

---

## Why the runtime lands in Phase D

Without a runtime, every capability is a pipeline. Pipelines don't compose. They don't audit. They don't extend without restructuring.

Introducing the runtime in Phase D means every subsequent phase — multi-source ingest, claims, fact-checker, deepener — plugs into the same pattern. The alternative is bolting agents onto the v0.2.0 chat pipeline. That path produces two architectures in one codebase and a rewrite before Phase G.

Phase D locks the agent shape. Everything after adds agents and tools. The runtime does not change.

---

## Architecture

```
User: "go deep on KV Cache" (mode: concept)
        ↓
POST /api/agent { task_type: "research", topic: "KV Cache", mode: "concept" }
        ↓
Agent Dispatcher (core/runtime/)
  → validates task contract
  → instantiates Research Agent with tool allowlist: [retrieve, generate, ingest]
  → starts execution loop
        ↓
Research Agent execution:
  1. retrieve("KV Cache", k=5) → existing KB chunks (wraps v0.2.0 hybrid retrieval)
  2. generate(research_prompt + kb_context) → synthesized notes (wraps v0.2.0 Provider)
  3. generate(produce_artifact_prompt + notes) → structured HTML artifact
  4. ingest(artifact) → written to artifacts table (wraps v0.1.0 ingest)
  → return { artifact_slug, summary }
        ↓
Run persisted → agent_runs table (all tool calls logged)
        ↓
Teaching Agent dispatched automatically with artifact_slug
  1. retrieve(artifact_slug) → the notes just written
  2. generate(teach_layer_1_prompt + notes) → layer 1 teaching content
  3. [multi-turn loop via generate]
     → quiz, assess response, advance or remediate
  4. generate(connections_prompt + session_log) → concept connections
  5. generate(checklist_prompt + session_log) → mastery checklist
  6. ingest(checklist) → written to artifacts table
  → return { checklist_slug, mastery_level }
        ↓
Run persisted → agent_runs table
        ↓
Portal: artifact card for notes + artifact card for checklist
        both linked from the agent run history
```

---

## Core components

### core/runtime/ — Agent execution loop (NEW)

The dispatch function. Responsibilities:
- Receive a typed task contract
- Instantiate the correct agent with its tool allowlist
- Execute the agent loop — call tools, accumulate output, exit on finish or error
- Log every tool call to the run record
- Persist the completed run to `agent_runs`
- Return the AgentRun record to the caller

```python
@dataclass
class ToolCallRecord:
    tool_name: str
    input: dict
    output: dict
    success: bool
    error: str | None
    tokens_used: int
    called_at: str

@dataclass
class AgentRun:
    id: int | None
    agent_type: str
    task_input: dict
    status: Literal["running", "complete", "failed"]
    output: dict | None
    error: str | None
    tool_calls: list[ToolCallRecord]
    cost_tokens: int
    cost_usd: float
    started_at: str
    finished_at: str | None

def dispatch(task: ResearchTask | TeachTask) -> AgentRun:
    """Dispatch a task to the correct agent and run to completion."""
```

The loop is synchronous in Phase D. Async is earned in Phase G when agents run without explicit user invocation.

### core/runtime/contracts.py — Typed task contracts (NEW)

```python
from dataclasses import dataclass
from typing import Literal

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

Contracts are validated at dispatch time. Invalid contract raises before any LLM call is made.

### core/tools/ — Tool interface and Phase D implementations (NEW)

```python
from typing import Protocol

class Tool(Protocol):
    name: str
    description: str
    def execute(self, input: dict) -> dict: ...
```

**Tool router:** maintains a registry of all registered tools. Each agent receives an allowlist of tool names. Calling a tool not in the allowlist raises immediately — not silently ignored.

**Phase D tools (each wraps existing v0.2.0 / v0.1.0 code):**

`retrieve` — wraps the v0.2.0 hybrid retrieval pipeline
- Input: `{ query: str, k: int = 5 }`
- Output: `{ results: list[{ chunk_id, artifact_id, slug, title, snippet, score }] }`
- Implementation: calls existing hybrid retrieval (vector + FTS5 + score-based merge) from v0.2.0
- **No retrieval rebuild.** The Tool interface is the thin wrapper.

`generate` — wraps the v0.2.0 Provider abstraction
- Input: `{ messages: list[{ role, content }], context: list[dict] | None }`
- Output: `{ text: str, tokens_used: int, cost_usd: float }`
- Implementation: calls existing `Provider.chat()` from v0.2.0 (Bedrock default)
- **No Provider rewrite.** The Tool interface wraps the existing Provider.

`ingest` — wraps the v0.1.0 ingest logic
- Input: `{ title: str, slug: str, html_content: str, summary: str, tags: list[str] }`
- Output: `{ artifact_id: int, slug: str, success: bool }`
- Implementation: calls existing ingest logic, writes to `artifacts` table

### core/prompts/ — Skill-embedded prompt templates (NEW)

Prompt templates for both agents. The research-wiki and teach-me skill instructions are embedded here as system prompts — not inline in agent code.

Phase D ships:
- `RESEARCH_SYSTEM` — research agent system prompt with research-wiki skill embedded
- `RESEARCH_PRODUCE` — prompt for producing the final HTML artifact from synthesized notes
- `TEACH_SYSTEM` — teaching agent system prompt with teach-me skill embedded
- `TEACH_LAYER` — prompt for each teaching loop iteration

Skills update here. The runtime does not change when skills change.

### core/llm/bedrock.py — Already shipped in v0.2.0

No changes in Phase D. The existing Provider abstraction is wrapped by the `generate` tool.

Current providers in v0.2.0:
- `BedrockProvider` (only implementation) — Claude Sonnet 4.6 for chat, Cohere Embed v4 (1024 dims) for embeddings via boto3

Selected via `EVO_LLM_PROVIDER` env var (default `bedrock`). AWS credentials validated at boto3 client creation. Note: `anthropic` and `openai` packages are NOT in `pyproject.toml` — they were removed in the Bedrock pivot (commit `59989c0`).

---

## The two agents

### Research Agent

**Task:** ResearchTask
**Allowlist:** `retrieve`, `generate`, `ingest`
**Skill:** research-wiki (embedded in RESEARCH_SYSTEM)

**Execution flow:**
```
1. retrieve(topic, k=5)
   → existing KB chunks on this topic and related concepts
2. generate(RESEARCH_SYSTEM + topic + kb_context)
   → synthesized research notes
3. generate(RESEARCH_PRODUCE + notes)
   → structured HTML artifact (sections per research-wiki skill)
4. ingest(html_artifact, title, slug, summary, tags)
   → artifact written to KB
5. return { artifact_slug, artifact_id, summary }
```

**Output:** one structured notes artifact in KB + run log entry in `agent_runs`

Note on `web_search`: The Research Agent is designed to call `web_search` as its first tool in Phase G. In Phase D the tool is not registered — the agent retrieves KB context only. Phase D research sessions are useful for topics already partially in the KB. Phase G unlocks full research from scratch.

### Teaching Agent

**Task:** TeachTask
**Allowlist:** `retrieve`, `generate`, `ingest`
**Skill:** teach-me (embedded in TEACH_SYSTEM)

**Execution flow:**
```
1. retrieve(topic or artifact_slug, k=8)
   → notes on this topic from KB (uses v0.2.0 hybrid retrieval)
2. generate(TEACH_SYSTEM + notes + mastery_context)
   → layer 1 teaching content
3. [multi-turn teaching loop]
   → each turn: generate(TEACH_LAYER + session_log + user_response)
   → quiz user, assess answer, advance layer or remediate
   → loop exits when all layers mastered or max turns reached
4. generate(connections_prompt + session_log)
   → concept connections to previously mastered topics
5. generate(checklist_prompt + session_log)
   → mastery checklist markdown
6. ingest(checklist_artifact)
   → checklist written to KB
7. return { checklist_slug, mastery_level, concepts_connected }
```

**Teaching loop mechanics:** The session is multi-turn within a single agent run. The portal sends user responses via `POST /api/agent/[run_id]/message`. Each message is appended to the conversation and fed into the next `generate` call. The run stays open until the session completes (all layers verified) or max turns is reached (`EVO_TEACH_MAX_TURNS`, default 20).

**Output:** one mastery checklist artifact in KB + run log entry in `agent_runs`

---

## Auto-chain: Research → Teaching

When a Research run completes successfully, the system automatically dispatches a Teaching run with the produced `artifact_slug`. This is the core loop made automatic.

The user can opt out via `{ auto_teach: false }` in the research request. Default is `true`.

---

## Schema additions (migration 003)

```sql
-- Migration 003 (Phase D)
-- Note: migration 002 (chunks + embeddings + claims stub — all in one file) shipped in v0.2.0

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

CREATE INDEX idx_agent_runs_type   ON agent_runs(agent_type);
CREATE INDEX idx_agent_runs_status ON agent_runs(status);
```

No new `chunks`, `embeddings`, or `claims` work in Phase D. Those tables already exist from v0.2.0 (chunks + embeddings active; claims stub waiting for Phase F).

---

## API

### POST /api/agent — dispatch an agent run

Request:
```typescript
{
  task_type: "research" | "teach";
  topic: string;
  mode?: "concept" | "tool" | "company";   // research only
  artifact_slug?: string;                   // teach only — teach from this artifact
  context?: string;
  mastery_context?: string;
  auto_teach?: boolean;                     // default true for research tasks
}
```

Response:
```typescript
{
  run_id: number;
  status: "running" | "complete" | "failed";
  output?: {
    artifact_slug?: string;
    checklist_slug?: string;
    summary?: string;
  };
  error?: string;
  cost_tokens: number;
  cost_usd: number;
}
```

### POST /api/agent/[run_id]/message — send teaching session response

Request: `{ content: string }`
Response: `{ reply: string; status: "teaching" | "complete" | "failed" }`

### GET /api/agent/[run_id] — poll run status

Returns same shape as POST /api/agent response.

### GET /api/agent/runs — run history

```typescript
{
  runs: Array<{
    id: number;
    agent_type: string;
    status: string;
    cost_usd: number;
    started_at: string;
    output_slug?: string;
  }>;
  total: number;
}
```

### Existing endpoints unchanged

- `POST /api/chat` — stays from v0.2.0, no changes. Framing updates only.
- `/chat` portal route — stays from v0.2.0. Nav and on-page copy update to "Query what agents built."

---

## Portal additions

### /agent — primary interface (NEW)

- Topic input
- Task type selector (Research / Teaching)
- Mode selector for research (concept / tool / company)
- Context field (optional — user's direction or existing knowledge)
- Auto-teach toggle (default on)
- Submit → dispatch → status display (running / complete / failed)
- On complete: link to produced artifact + link to mastery checklist (if auto-teach ran)
- On failed: error message + tool call log for debugging

### Artifact viewer — "Teach me this" button (NEW)

Every artifact gets a "Teach me this" button. One click pre-fills the Teaching Agent form with the artifact slug and navigates to `/agent`.

### Run history sidebar (NEW)

Recent agent runs with type badge, status badge, cost, and output links.

### Navigation update

`/agent` becomes the primary nav item. `/chat` moves to secondary position with framing "Query what agents built."

---

## Files to create

```
core/
  runtime/
    loop.py         — execution loop, tool dispatch, run logging, DB persistence
    contracts.py    — ResearchTask, TeachTask
    dispatcher.py   — task dispatch + Research→Teaching chain
  tools/
    base.py         — Tool protocol
    retrieve.py     — wraps core/memory/retrieval.py
    generate.py     — wraps core/llm/
    ingest.py       — wraps scripts/ingest.py logic
    web_search.py   — stub → real Phase G
  prompts/
    templates.py    — skill-embedded prompt templates
    research_wiki.md — Research Agent skill
    teach_me.md     — Teaching Agent skill
  governance/
    audit.py        — agent_runs logging + cost tracking
    allowlist.py    — per-agent tool permissions
agents/
  research.py       — Research Agent
  teaching.py       — Teaching Agent
scripts/
  migrations/
    003_phase_d.sql
  agent.py          — CLI for dispatching agent runs from terminal
tests/
  test_runtime.py
  test_contracts.py
  test_tools.py
portal/
  app/
    agent/
      page.tsx
    api/
      agent/
        route.ts
        [run_id]/
          route.ts
          message/
            route.ts
        runs/
          route.ts
  components/
    agent-form.tsx
    run-status.tsx
    run-history.tsx
    teach-session.tsx   — multi-turn teaching session UI
  lib/
    agent-client.ts
  __tests__/
    api/
      agent.test.ts
```

## Files to modify

```
core/llm/bedrock.py           — no changes; tools/generate wraps it
scripts/ingest.py         — extract shared DB helpers if needed for tools/ingest wrapper
server.py            — no changes (file at repo root, not scripts/)
CHANGELOG.md              — Phase D entry under [Unreleased]
CLAUDE.md                 — already updated (Phase D active)
portal/app/layout.tsx     — add /agent as primary nav link, move /chat to secondary
portal/app/[slug]/page.tsx — add "Teach me this" button
portal/app/chat/page.tsx  — update header copy: "Query what agents built"
```

## Files NOT to touch

- `core/llm/bedrock.py` — already shipped in v0.2.0, do not rewrite
- `core/memory/retrieval.py` (or wherever hybrid retrieval lives) — already shipped in v0.2.0, wrapped by `tools.retrieve`
- `scripts/embed.py` — already shipped, no changes
- Migrations 001 + 002 — already applied, do not modify
- Phase C eval harness — runs against Phase D as regression gate, no rewrite

---

## Environment variables

```bash
# Already configured in v0.2.0 (no changes in Phase D)
AWS_PROFILE=my-bedrock-profile
AWS_REGION=us-east-1
EVO_LLM_PROVIDER=bedrock          # 'bedrock' (only implemented provider)

# New in Phase D
EVO_TEACH_MAX_TURNS=20            # max turns before teaching session closes
```

All validated at startup. Loud failure if required vars missing. No silent fallback.

---

## Dependencies

Dependencies that already exist in `pyproject.toml` from v0.2.0 (do not re-add):
- `anthropic` (direct API support)
- `boto3` / `botocore` (Bedrock)
- `fastapi`, `uvicorn`, `pydantic`
- All test infra

Dependencies that may need to be added in Phase D (Hermes decides during plan):
- Agent framework dependency, **if** the open question on agent loop is resolved as "wrap existing primitive" rather than "custom Python loop"
  - Candidates: `smolagents`, `pydantic-ai`, `langgraph`
  - Default recommendation: custom Python loop (no new dep) — keeps the runtime on the critical learning path

---

## Testing

**Python (pytest):**
- `test_runtime.py` — dispatch with mock agents, execution loop, tool call logging, run persistence, error handling, auto-chain behavior
- `test_contracts.py` — valid contracts, invalid contracts, missing required fields
- `test_tools.py` — retrieve wraps Phase C retrieval correctly, ingest writes to DB idempotently, generate wraps Phase C Provider and returns cost metadata, allowlist enforcement raises on unlisted tool
- Existing test suite (84 tests from v0.2.0, 2 skipped) — all must continue to pass

Coverage: new modules at 100%, runtime at ≥ 95%

**TypeScript (vitest):**
- `agent.test.ts` — POST dispatch, GET status poll, message endpoint, invalid task rejection, run history pagination
- Existing portal tests — all must continue to pass

**Phase C eval regression:**
- 10-question retrieval eval from v0.2.0 must still score 10/10 after Phase D merge
- This is a non-negotiable gate. Failing eval = Phase D does not tag.

---

## Acceptance criteria

- [ ] Migration 003 applies cleanly to fresh DB and existing v0.2.0 vault
- [ ] Research Agent completes end-to-end: ResearchTask → artifact in KB → run log entry
- [ ] Teaching Agent completes end-to-end: TeachTask → mastery checklist in KB → run log entry
- [ ] Auto-chain works: Research run completion automatically dispatches Teaching run
- [ ] Every tool call recorded in `agent_runs.tool_calls`
- [ ] Tool allowlist enforced — calling unlisted tool raises immediately, does not silently ignore
- [ ] Failed run records error + all tool calls made before failure
- [ ] Agent runs visible in portal: status, cost, output links
- [ ] "Teach me this" button on artifact viewer dispatches teaching run
- [ ] Existing chat surface still works (no regressions in `/chat`)
- [ ] Phase C eval harness still passes 10/10 — no retrieval quality regression
- [ ] All new tests pass; existing 84 Python tests still pass; CI green
- [ ] No regressions in Phase A/B portal functionality
- [ ] `retrieve`, `generate`, `ingest` tools wrap existing v0.2.0/v0.1.0 code — no rebuild
- [ ] Samuel completes 3 Research runs + 3 Teaching runs on real topics before tagging v0.3.0
- [ ] CHANGELOG entry for v0.3.0 complete
- [ ] CLAUDE.md updated — Phase D shipped, Phase E next

---

## Risks

| Risk | Mitigation |
|---|---|
| Tool wrappers diverge from underlying v0.2.0 implementations | `tools.retrieve` etc. directly import and call existing functions. No copy-paste. |
| Phase C eval breaks after Phase D merge | Eval runs in CI on every PR. Phase D does not tag until 10/10 passes. |
| Teaching loop never exits | `EVO_TEACH_MAX_TURNS` cap. Run marked complete on limit. |
| Agent loop too rigid for varied agent behavior | Tool allowlist per agent gives flexibility. Runtime loop is generic. |
| Cost accumulates without visibility | cost_tokens and cost_usd tracked from run 0 and displayed in portal. Caps come in Phase G. |
| Auto-chain teaching run fails after successful research | Research run marked complete regardless. Teaching failure logged separately. User can manually dispatch teaching from the artifact. |
| Existing `/chat` confuses users about which interface is primary | Nav update makes `/agent` primary. `/chat` header copy clarifies "Query what agents built." |

---

## Open questions (Hermes resolves before kickoff)

1. **Agent loop** — custom Python execution loop (recommended) or thin wrapper over smolagents / pydantic-ai / LangGraph? Custom keeps the runtime on the critical learning path and avoids a framework dependency in core. Wrap option saves implementation time but introduces lock-in.
2. **Teaching session turn handling** — portal polling (recommended for Phase D) or WebSocket? WebSocket is cleaner but adds complexity; earn it in Phase D.1 patch or Phase E.
3. **Auto-chain default** — should Research → Teaching auto-chain be on by default or opt-in? Recommend on by default — it is the core loop. Users who want research-only can toggle off.
4. **Tool wrapper location** — does `tools.retrieve` live as a function in `core/tools/` or as a class method? Recommendation: function with closures over the existing retrieval implementation. Cleaner imports, easier testing.
5. **Migration hygiene** — should Hermes extract the inline `artifacts` schema from `ingest.py` into a new `001_initial.sql` migration as part of Phase D, or leave the current arrangement alone? Currently migration 002 depends on the `artifacts` table which is created inline by `ingest.py`'s `_SCHEMA`, not by any migration file. Recommend: leave alone for v0.3.0, address in Phase H portability work when fresh-install testing happens.

---

## Working agreement

- **Hermes (PM)** — produces `tasks/plan-phase-d.md` resolving the open questions above before any code is written
- **Claude Code (SWE)** — implements per this spec; raises any architectural deviation as a question, not a silent change
- **Samuel (PO)** — reviews plan before implementation begins; signs off after acceptance criteria pass
