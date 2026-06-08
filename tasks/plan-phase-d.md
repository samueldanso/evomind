# Phase D — Agent Foundation — Implementation Plan (v0.3.0)

> Hermes (PM) owns this doc. Claude Code reads it before writing a line.
> Spec: [specs/phase-d-agent-foundation.md](../specs/phase-d-agent-foundation.md)
> Samuel signs off before implementation starts.

---

## Open questions — resolved

**1. Agent loop — custom Python or framework wrapper?**

→ **Custom Python execution loop.** No smolagents, no pydantic-ai, no LangGraph.

This is not an implementation shortcut decision. EvoResearch is being built as an AI Platform Engineering portfolio artifact. The engineering thesis — *Agent = LLM + Harness* — requires building the harness. A framework wrapper demonstrates configuration skill, not platform engineering. The loop itself (`core/runtime/loop.py`) is the critical learning path: observe → reason → act, tool dispatch, run logging, error handling, cost accumulation. Every subsequent phase (Fact-Checker, Deepener, Reconciler) slots into this loop without restructuring. Custom keeps the runtime fully auditable, no abstraction tax, no version drift.

Dependencies: none new for the loop itself.

**2. Teaching session turns — polling or WebSocket?**

→ **Portal polling for Phase D.** `GET /api/agent/[run_id]` on a 2-second interval. Teaching session turn delivery via the `POST /api/agent/[run_id]/message` response body (synchronous round-trip — user sends a message, gets the next teaching turn back in the response). Polling for run status visibility.

WebSocket is cleaner UX but adds server-side connection lifecycle management in FastAPI and client-side WebSocket handling in Next.js — real complexity for a solo local tool. The synchronous message/response pattern is natural for a teaching session anyway: the agent waits for the student. Earn WebSocket in Phase D.1 or Phase G when async execution lands.

**3. Auto-chain Research → Teaching — default on or opt-in?**

→ **Default on.** `auto_teach: true` is the default. Users pass `auto_teach: false` to opt out.

The core loop *is* Research → Teaching → KB compounds. Making it opt-in means users miss the compound effect by default. The product is the loop, not the individual agents. Cost is tracked and displayed — the user sees exactly what auto-chain costs. Anyone who wants research-only can toggle off.

**4. Tool wrapper location — function with closures or class method?**

→ **Functions with closures.** Each tool module (`core/tools/retrieve.py` etc.) exports a factory function that returns a closure over the underlying v0.2.0 implementation.

```python
# core/tools/retrieve.py
def build_retrieve_tool(db: sqlite3.Connection, provider: Provider) -> Tool:
    def execute(input: dict) -> dict:
        return hybrid_retrieve(db, input["query"], provider, k=input.get("k", 5))
    return Tool(name="retrieve", description="...", execute=execute)
```

Import: `from core.tools.retrieve import build_retrieve_tool`. Clean, no OOP boilerplate, matches the existing codebase style (functional Python), trivially mockable in tests (replace the closure with a mock function). Classes add no value here.

**5. Migration hygiene — extract `artifacts` schema to 001_initial.sql or leave?**

→ **Leave alone. Address in Phase H portability work.**

Migration 002 correctly depends on the `artifacts` table already existing (created inline by `ingest.py`'s `_SCHEMA`). This is a known debt, not a bug — the vault already has a working DB and migration 002 is applied. Extracting to `001_initial.sql` is portability work: it matters when fresh installs from scratch need a clean migration chain. That's Phase H. Doing it now would add a migration refactor with zero user value and non-trivial risk to a working DB. Document the arrangement in the migration file header comment and leave it.

---

## Pre-flight checklist (before T1)

- [x] v0.2.0.1 patch (vitest → bun:sqlite fix, all 37 portal tests green) — merged, tagged, pushed
- [ ] `uv run pytest` passes — 84 tests green (baseline before any changes)
- [ ] `cd portal && bun test && bun run build` passes — baseline
- [ ] `uv run scripts/eval.py` passes — 10/10 retrieval eval (baseline)
- [ ] Vault DB backed up: `cp manifest.db manifest.db.bak`
- [ ] `AWS_PROFILE=my-bedrock-profile` and `AWS_REGION=us-east-1` confirmed in env

---

## Task breakdown for Claude Code

Tasks are ordered — each builds on the previous. Do not skip ahead. Commit at the end of each logical unit within a task. Run `uv run pytest && cd portal && bun test && bun run build` before every commit.

---

### T1 — Migration + contracts + governance (size: small, ~12 turns)

**What:** Land the agent_runs schema, typed task contracts, and the governance layer (allowlist enforcement + audit logging). No agent code yet — only the primitives agents depend on.

**Files to create:**

`scripts/migrations/003_phase_d.sql`
- `agent_runs` table (exact schema from spec)
- `idx_agent_runs_type` and `idx_agent_runs_status` indexes
- Header comment: "Migration 003 — Phase D — depends on artifacts table created by ingest.py _SCHEMA (not a migration file). This is a known arrangement addressed in Phase H portability work."

`core/runtime/contracts.py`
- `ResearchTask` dataclass: `task_type: Literal["research"]`, `topic: str`, `mode: Literal["concept", "tool", "company"]`, `context: str | None = None`
- `TeachTask` dataclass: `task_type: Literal["teach"]`, `topic: str`, `artifact_slug: str | None = None`, `mastery_context: str | None = None`
- `validate_task(task)` function — raises `ValueError` with clear message on invalid contract. Called at dispatch time before any LLM call.

`core/governance/allowlist.py`
- `AGENT_ALLOWLISTS: dict[str, list[str]]` — `research_agent: ["retrieve", "generate", "ingest"]`, `teaching_agent: ["retrieve", "generate", "ingest"]`
- `check_allowlist(agent_type: str, tool_name: str) -> None` — raises `PermissionError` immediately if tool not in allowlist. Not silently ignored.

`core/governance/audit.py`
- `create_run(db, agent_type, task_input) -> int` — inserts agent_runs row with status=running, returns run_id
- `record_tool_call(db, run_id, record: ToolCallRecord) -> None` — appends to `agent_runs.tool_calls` JSON array atomically
- `complete_run(db, run_id, output, cost_tokens, cost_usd) -> None` — sets status=complete, finished_at, output
- `fail_run(db, run_id, error, cost_tokens, cost_usd) -> None` — sets status=failed, error, finished_at
- `get_run(db, run_id) -> dict | None`
- `list_runs(db, limit=20) -> list[dict]`

`core/runtime/__init__.py` — modify if needed (already exists from v0.2.0 restructure), `core/governance/__init__.py` — create new

**Files to modify:**

`scripts/migrate.py` — confirm it applies 003_phase_d.sql cleanly. If it loads sqlite-vec, confirm the extension path is consistent with how v0.2.0 does it (migration 003 does not use sqlite-vec, but migrate.py must load the extension for 002's sake).

**Tests to create:**

`tests/test_contracts.py`
- Valid ResearchTask (all modes), valid TeachTask, missing required fields raise ValueError, invalid mode raises ValueError, extra fields tolerated (dataclass default)

`tests/test_governance.py`
- Allowlist: research_agent can call retrieve/generate/ingest, raises on web_search (not in allowlist)
- Audit: create_run returns int, record_tool_call appends to JSON, complete_run updates status, fail_run records error, get_run returns correct shape, list_runs returns ≤ limit entries

**Acceptance:**
- `uv run scripts/migrate.py` applies 003 to fresh DB and to existing vault DB
- Idempotent — second apply does not raise
- `agent_runs` table exists with correct schema after migration
- All new tests pass; existing 84 tests still pass

---

### T2 — Tool layer (size: small, ~12 turns)

**What:** The four Phase D tools, each wrapping existing v0.2.0/v0.1.0 code under the Tool protocol. The `web_search` stub. No agents yet — only the tool interface.

**Tool wrapper pattern (all four tools follow this):**

```python
# core/tools/<name>.py
from typing import Protocol
from dataclasses import dataclass

@dataclass
class Tool:
    name: str
    description: str
    execute: Callable[[dict], dict]
```

Each tool module exports a factory function (`build_retrieve_tool`, `build_generate_tool`, `build_ingest_tool`, `build_web_search_tool`). Factories take the dependencies they need (db, provider) as arguments and return closures. No global state.

**Files to create:**

`core/tools/base.py`
- `Tool` dataclass (as above)
- `ToolRegistry` — `register(tool: Tool)`, `get(name: str) -> Tool`, `build_for_agent(agent_type: str) -> dict[str, Tool]` — uses `AGENT_ALLOWLISTS` from governance

`core/tools/retrieve.py` — `build_retrieve_tool(db, provider) -> Tool`
- Input schema: `{ query: str, k: int = 5 }`
- Output: `{ results: list[{ chunk_id, artifact_id, slug, title, snippet, score, match_type }] }`
- Implementation: calls `hybrid_search` from `core/memory/retrieval.py`. **No retrieval rebuild.** Direct import + call.
- Returns empty results (not error) if corpus is empty

`core/tools/generate.py` — `build_generate_tool(provider) -> Tool`
- Input schema: `{ messages: list[{ role: str, content: str }], context: list[dict] | None }`
- Output: `{ text: str, tokens_used: int, cost_usd: float }`
- Implementation: calls `provider.chat()` from `core/llm/bedrock.py`. **No Provider rewrite.** Direct import + call.
- Passes context chunks through to provider for grounded generation

`core/tools/ingest.py` — `build_ingest_tool(db, vault_path) -> Tool`
- Input schema: `{ title: str, slug: str, html_content: str, summary: str, tags: list[str] }`
- Output: `{ artifact_id: int, slug: str, success: bool }`
- Implementation: reuses existing ingest logic from `scripts/ingest.py` (extract the core upsert function into `core/memory/db.py` if not already there, import it here). **No rewrite.**
- After ingest: triggers `chunk_and_store` (same as the CLI ingest path)

`core/tools/web_search.py` — `build_web_search_tool() -> Tool`
- Phase D stub — always returns `{ results: [] }`
- Comment: "Phase G: replace with real web_search (Brave/Tavily/Exa)."
- Registered in tool registry but NOT in any agent's allowlist for Phase D

`core/tools/__init__.py`

**Tests to create:**

`tests/test_tools.py`
- `build_retrieve_tool`: returns Tool protocol, execute calls hybrid_search (spy/mock), returns correct output shape, empty corpus returns empty results not error
- `build_generate_tool`: returns Tool protocol, execute calls provider.chat (spy/mock), returns cost metadata in output
- `build_ingest_tool`: returns Tool protocol, execute writes to DB, idempotent on same slug
- `build_web_search_tool`: returns empty results always
- `ToolRegistry`: register + get round-trip, build_for_agent respects allowlist, unknown tool raises KeyError
- Allowlist enforcement via check_allowlist: calling unregistered tool raises PermissionError

Use `MockProvider` pattern (already exists in v0.2.0 test suite behind `RUN_LIVE_LLM=1`). All Phase D tests use mock — no real API calls in CI.

**Checkpoint A — Evo reviews after T2:**
Evo reads `core/tools/retrieve.py`, `core/tools/generate.py`, `core/tools/ingest.py` and confirms each is a thin closure over the existing v0.2.0 implementation, not a rewrite. If any tool re-implements retrieval logic, stop and correct before T3.

---

### T3 — Agent execution loop + prompts (size: medium, ~15 turns)

**What:** The runtime loop that agents run through. The skill-embedded prompt templates. This is the architectural center of Phase D — the observe-reason-act cycle made concrete.

**Files to create:**

`core/prompts/research_wiki.md` — research-wiki skill
The instruction set the Research Agent follows. What sections to produce. How to write for future retrieval. Structure:
- Summary (2-3 sentences, dense, searchable)
- Core Concepts (numbered, each with definition + why it matters)
- How It Works (mechanism-level explanation)
- Tradeoffs and Limitations
- Connections to Adjacent Concepts (what this links to)
- Sources and Context (what was used to produce this note)
Write this as the actual skill content — detailed, not a placeholder.

`core/prompts/teach_me.md` — teach-me skill
The instruction set the Teaching Agent follows. Layer-by-layer teaching. Problem before solution. Quiz before advancing. Connection step at end of every session. Structure:
- Opening: assess existing knowledge
- Layer 1 → N: each layer teaches one concept increment; quiz before advancing
- On wrong answer: remediate, don't skip
- Connections: map to what the learner already knows
- Closing: produce mastery checklist
Write this as the actual skill content — detailed, not a placeholder.

`core/prompts/templates.py`
- `RESEARCH_SYSTEM` — loads research_wiki.md content, embeds as system prompt with instructions for the Research Agent
- `RESEARCH_PRODUCE` — prompt template for producing the final structured HTML artifact from synthesized notes. Includes the research_wiki schema sections.
- `TEACH_SYSTEM` — loads teach_me.md content, embeds as system prompt with instructions for the Teaching Agent. Includes mastery_context if provided.
- `TEACH_LAYER` — prompt template for each teaching loop turn. Takes: session_log, user_response. Returns: next teaching layer or quiz or assessment.
- `TEACH_CONNECTIONS` — prompt for generating concept connection map from completed session
- `TEACH_CHECKLIST` — prompt for generating mastery checklist from completed session

`core/runtime/loop.py`
The execution loop. Core interface:

```python
def run_agent(
    agent_type: str,
    task: ResearchTask | TeachTask,
    tools: dict[str, Tool],
    db: sqlite3.Connection,
) -> AgentRun:
    """Execute an agent loop to completion. Returns the completed AgentRun."""
```

Responsibilities:
- Start a run record (`audit.create_run`)
- Execute the agent's step function in a loop
- For each tool call: validate against allowlist, execute, record via `audit.record_tool_call`
- On completion: call `audit.complete_run`, return AgentRun
- On any exception: call `audit.fail_run`, re-raise (caller handles)
- Loop is synchronous (Phase D). No async.

`core/runtime/__init__.py` — re-exports

**Tests to create:**

`tests/test_runtime.py`
- `run_agent` with mock Research Agent: loop runs, all tool calls recorded, run marked complete
- `run_agent` with mock Teaching Agent: multi-turn session, all turns recorded, run marked complete on max_turns
- `run_agent` when tool raises: run marked failed, error recorded, all tool calls before failure are in the log
- Allowlist check at tool call time (not just at dispatch): calling an unlisted tool from inside the loop raises and fails the run
- Cost accumulation: tokens_used and cost_usd sum correctly across multiple generate calls in one run

**Acceptance:**
- `run_agent` with mock tools runs end-to-end without real LLM calls
- Failed run has correct status, error, and partial tool_calls log
- All new tests pass; existing 84 tests still pass

---

### T4 — Research Agent + Teaching Agent + Dispatcher (size: medium, ~15 turns)

**What:** The two agents and the dispatcher that chains them. This is where the product behavior is defined.

**Files to create:**

`core/agents/research.py` — Research Agent
Execution flow (each step is a tool call via the loop):
1. `retrieve(topic, k=5)` → existing KB chunks as context
2. `generate(RESEARCH_SYSTEM + topic + kb_context)` → synthesized research notes
3. `generate(RESEARCH_PRODUCE + notes)` → structured HTML artifact
4. `ingest(html_artifact, title, slug, summary, tags)` → written to KB
5. Return `{ artifact_slug, artifact_id, summary }`

The agent's step function is called by `run_agent`. It receives the current tool registry and produces either a tool call or a final result. Simple finite state machine — no recursion.

`core/agents/teaching.py` — Teaching Agent
Execution flow:
1. `retrieve(topic or artifact_slug, k=8)` → notes from KB
2. `generate(TEACH_SYSTEM + notes + mastery_context)` → layer 1 content
3. Multi-turn loop: each turn receives user_response via task context, `generate(TEACH_LAYER + session_log + user_response)` → next turn
4. Loop exits on: all layers verified OR max_turns reached (from `EVO_TEACH_MAX_TURNS`, default 20)
5. `generate(TEACH_CONNECTIONS + session_log)` → concept connections
6. `generate(TEACH_CHECKLIST + session_log)` → mastery checklist markdown
7. `ingest(checklist_artifact)` → written to KB
8. Return `{ checklist_slug, mastery_level, concepts_connected }`

Teaching loop note: the multi-turn exchange is handled through the dispatcher endpoint — each `POST /api/agent/[run_id]/message` appends to the session log and feeds into the next generate call. The run stays in `running` status during active teaching. `run_agent` handles the turn loop internally for the Teaching Agent.

`core/runtime/dispatcher.py`
```python
def dispatch(
    task: ResearchTask | TeachTask,
    db: sqlite3.Connection,
    provider: Provider,
    auto_teach: bool = True,
) -> AgentRun | tuple[AgentRun, AgentRun]:
    """Dispatch task to correct agent. If Research + auto_teach=True, chain Teaching after."""
```

- Validates task contract
- Builds tool registry for the agent's allowlist
- Calls `run_agent`
- If Research task + auto_teach=True + research run succeeded: automatically dispatches TeachTask with `artifact_slug` from research output. Teaching failure is logged separately — research run is still marked complete.
- Returns single AgentRun (teach) or tuple (research, teaching) if chained

`scripts/agent.py` — CLI dispatch
```bash
uv run scripts/agent.py --task research --topic "KV Cache" --mode concept
uv run scripts/agent.py --task teach --topic "KV Cache"
uv run scripts/agent.py --task research --topic "vLLM" --mode tool --no-auto-teach
```

**Tests:**

Extend `tests/test_runtime.py` (or new `tests/test_agents.py`):
- Research Agent: dispatch → mock tool calls in correct order → output has artifact_slug
- Teaching Agent: dispatch → multi-turn session → checklist output
- Dispatcher auto-chain: research succeeds → teaching auto-dispatched with correct artifact_slug
- Dispatcher auto-chain opt-out: `auto_teach=False` → only research runs
- Dispatcher: teaching failure after research success → research AgentRun still marked complete, teaching AgentRun marked failed separately

**Checkpoint B — Evo reviews after T4:**
Evo runs `uv run scripts/agent.py --task research --topic "vLLM" --mode tool` via CLI with real Bedrock (cost-aware). Confirms: artifact written to KB, run recorded in agent_runs, cost_tokens and cost_usd populated. If output quality is wrong, adjust RESEARCH_SYSTEM prompt before portal work begins.

---

### T5 — server.py → server/ + agent API routes (size: medium, ~15 turns)

**What:** Restructure server.py into a proper module (Phase D threshold), add all agent API endpoints. This is the last time server structure changes — the `/agent` route is the threshold.

**Server restructure (CLAUDE.md rule: "server.py → server/ when /agent route lands in Phase D"):**

```
server/
  __init__.py      — exports `app` (FastAPI instance)
  config.py        — EVO_CHAT_PORT, EVO_TEACH_MAX_TURNS, EVO_RESEARCH_STORE, startup validation
  utils.py         — shared helpers (DB open, provider init)
  routes/
    __init__.py
    chat.py        — existing POST /chat from server.py (moved, no logic change)
    agent.py       — new agent routes (POST /api/agent, GET /api/agent/[run_id], etc.)
```

**Rule for the move:** `routes/chat.py` is the existing `POST /chat` handler moved verbatim. No logic change. Import paths updated. Tests must still pass after move.

`server/routes/agent.py` — agent API routes

`POST /api/agent`
- Validate request shape (pydantic or manual validation — existing codebase uses manual, stay consistent)
- Build ResearchTask or TeachTask from request body
- Call `dispatcher.dispatch(task, db, provider, auto_teach=request.auto_teach)`
- Return AgentRun in response shape (see spec)
- If synchronous (Research Agent without teaching loop): waits for completion, returns complete run
- If auto_teach=True: returns after both research + teaching complete
- Note: Phase D is synchronous. Long-running? The CLI is the escape hatch. Portal shows spinner.

`GET /api/agent/{run_id}`
- Returns `audit.get_run(db, run_id)` in response shape
- 404 if not found

`POST /api/agent/{run_id}/message`
- Request: `{ content: str }`
- Appends user response to the teaching session, triggers next teaching loop turn
- Returns `{ reply: str, status: "teaching" | "complete" | "failed" }`
- Used for multi-turn teaching session turns

`GET /api/agent/runs`
- Returns `audit.list_runs(db, limit=20)` in response shape
- Supports `?limit=N` query param

**Portal API routes:**
Next.js route handlers in `portal/app/api/agent/`. They proxy to the FastAPI server (same pattern as existing `/api/chat` → `server.py`).

- `portal/app/api/agent/route.ts` — POST dispatch, GET runs
- `portal/app/api/agent/[run_id]/route.ts` — GET status poll
- `portal/app/api/agent/[run_id]/message/route.ts` — POST turn message
- `portal/lib/agent-client.ts` — typed TypeScript client for all agent endpoints

**Tests:**
`tests/test_server.py` (extend or create)
- POST /api/agent with valid ResearchTask → returns run with status
- POST /api/agent with invalid task → 422
- GET /api/agent/{run_id} → returns run
- GET /api/agent/{run_id} unknown → 404
- POST /api/agent/{run_id}/message → returns reply
- GET /api/agent/runs → returns list

`portal/__tests__/api/agent.test.ts`
- POST dispatch, GET status, message endpoint, run history — same pattern as existing `chat.test.ts`

**Acceptance:**
- Existing `POST /chat` still works after server restructure (no regressions)
- New agent endpoints return correct shapes
- `uvicorn server:app --port 8765` still works (app exported from `server/__init__.py`)
- Root `server.py` deleted after restructure — `server/` package is the sole entry point

---

### T6 — Portal UI (size: medium, ~15 turns)

**What:** The agent invocation surface — the primary interface. Navigation update. "Teach me this" button. Run history. Teaching session UI.

**Files to create:**

`portal/app/page.tsx` — agent invocation page (replaces current home/artifact grid)
- Topic input (text field)
- Task type selector (Research / Teaching) — radio or segmented control
- Mode selector for Research (concept / tool / company) — shows only when task=Research
- Artifact slug field — shows only when task=Teaching (pre-filled by "Teach me this" button)
- Context field (optional, text area)
- Auto-teach toggle — default on, shows only when task=Research
- Submit button → dispatches via `POST /api/agent`
- Status display: loading spinner during run, complete state with output links, failed state with error
- On Research complete: link to produced artifact + link to mastery checklist (if auto-teach ran)
- On Teaching complete: link to mastery checklist

`portal/components/agent-form.tsx` — the form component (extracted from page.tsx)

`portal/components/run-status.tsx` — displays running/complete/failed state, polls `GET /api/agent/[run_id]` every 2 seconds while status=running

`portal/components/run-history.tsx` — sidebar list of recent runs. Type badge (Research/Teaching), status badge, cost_usd, link to output artifact. Data from `GET /api/agent/runs`.

`portal/components/teach-session.tsx` — multi-turn teaching session UI. Shows teaching content from the agent, text input for responses, submit → `POST /api/agent/[run_id]/message` → renders reply. Visible only when an active teaching run is in progress.

**Files to modify:**

`portal/app/layout.tsx`
- `/agent` moves to primary nav (first item, or bold/emphasized)
- `/chat` moves to secondary position
- `/kb` — rename artifact grid route from `/` to `/kb` (CLAUDE.md: "Artifact grid moves to `/kb`. Chat at `/chat`. Run history at `/runs`.")
- Wait — CLAUDE.md says: "Phase D UI: agent invocation is the home page (`/`). Artifact grid moves to `/kb`. Chat at `/chat`. Run history at `/runs`." So:
  - `/` becomes the agent invocation page
  - `/kb` becomes the artifact grid (moved from `/`)
  - `/chat` stays
  - `/runs` is the run history page (new)

`portal/app/page.tsx` — becomes `/agent` invocation or redirect to `/agent`. The current home page (artifact grid) moves to `/kb`.
`portal/app/kb/page.tsx` — artifact grid (moved from `portal/app/page.tsx`)
`portal/app/runs/page.tsx` — run history (new page using `run-history` component)

`portal/app/artifacts/[slug]/page.tsx` (or wherever the artifact viewer lives)
- Add "Teach me this" button — one click pre-fills Teaching Agent form with artifact_slug and navigates to `/agent`

`portal/app/chat/page.tsx`
- Update header/intro copy: "Query what agents built." Not the primary surface label anymore.

**Routing decision (locked):** `/` is the agent invocation page directly — `portal/app/page.tsx` becomes the agent invocation UI. No separate `/agent` route. No redirect. `/kb` is the artifact grid (moved from current `/`). `/chat` stays. `/runs` is run history. The `portal/app/agent/` directory listed in the spec is not created — the page lives at `portal/app/page.tsx`.

**Tests:**
No new vitest tests required beyond what already passes (existing grid/search/viewer tests). Confirm existing tests still pass after the route rename.

**Acceptance:**
- `/` renders agent invocation UI, accepts input, dispatches run, shows status, links to output on completion
- `/kb` shows artifact grid (same functionality as old `/`, no regression)
- `/chat` still works, header copy updated
- "Teach me this" button pre-fills and navigates correctly
- Navigation order correct: `/agent` primary, `/kb` and `/chat` secondary

**Checkpoint C — Evo reviews + Samuel first live test after T6:**
Evo reviews portal UI for spec compliance. Samuel does one Research run + one Teaching run via portal on a real topic. If the loop doesn't feel right, adjust prompt templates before hardening.

---

### T7 — Eval gate, hardening, CI, docs (size: small, ~12 turns)

**What:** Run the regression gates. Confirm everything passes. Complete the docs. Prepare to ship.

**Tasks:**

Run Phase C eval harness: `uv run scripts/eval.py` — must score 10/10. This is a non-negotiable gate. Phase D does not tag if eval regresses.

Run full test suite: `uv run pytest && cd portal && bun test && bun run build` — all must pass. Count: 84+ Python tests (new Phase D tests add to this count), existing vitest tests + new agent.test.ts.

CI check: `.github/workflows/ci.yml` — confirm new test files are included. If any new test requires additional setup (e.g., test DB initialization for agent_runs), update CI accordingly. `EVO_RESEARCH_STORE` must be set to a tmp path in CI.

**Files to modify:**

`CHANGELOG.md` — fill in `[0.3.0]` entry:
```markdown
## [0.3.0] - YYYY-MM-DD

### Added — Phase D: Agent Foundation

- `core/runtime/` — agent execution loop, typed task contracts, Research→Teaching dispatcher
- `core/tools/` — Tool protocol, retrieve/generate/ingest wrappers over v0.2.0 substrate, web_search stub
- `core/prompts/` — research-wiki and teach-me skill instructions embedded as system prompts
- `core/governance/` — per-agent tool allowlist enforcement, agent_runs audit log, cost tracking
- `core/agents/research.py` — Research Agent: retrieve → synthesize → ingest to KB
- `core/agents/teaching.py` — Teaching Agent: retrieve → multi-turn teach → quiz → mastery checklist → ingest
- `server/` — server.py restructured into server/ module (Phase D threshold); agent routes added
- `POST /api/agent` — dispatch research or teach task
- `GET /api/agent/{run_id}` — poll run status
- `POST /api/agent/{run_id}/message` — send teaching session turn
- `GET /api/agent/runs` — run history
- Migration 003 — `agent_runs` table with full audit log and cost fields
- Portal: `/agent` is the new home page (primary interface); `/kb` replaces `/` for artifact grid; `/runs` for run history
- "Teach me this" button on every artifact in the KB
- Auto-chain: Research run automatically dispatches Teaching run (default on, opt-out via `auto_teach: false`)
- Cost tracking from run zero: `cost_tokens` and `cost_usd` on every run

### Changed

- `server.py` → `server/` module (routes/chat.py, routes/agent.py, config.py, utils.py)
- Portal home page (`/`) → agent invocation; artifact grid moved to `/kb`
- `/chat` header copy updated: "Query what agents built."
- Navigation: `/agent` primary, `/kb` and `/chat` secondary

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `EVO_TEACH_MAX_TURNS` | `20` | Max teaching session turns before auto-close |

### Tests

- N Python tests (was 84; includes new runtime, contracts, governance, tools, agents)
- N portal vitest tests

### Notes

- `web_search` tool is a stub returning empty results in Phase D. Real implementation lands in Phase G.
- Agent loop is synchronous in Phase D. Async runtime lands in Phase G.
- v0.2.0 retrieval pipeline and Provider abstraction unchanged — Phase D wraps them under Tool interfaces.
```

`CLAUDE.md` — update "Current state" section: Phase D shipped, Phase E next.

`README.md` — add Phase D commands + update architecture diagram status from 🟡 to ✅ for Phase D components.

`.conductor/settings.toml` — create placeholder (committed to repo). Conductor is deferred to post-Phase D but the config file is committed now so workspace config is ready when adoption decision is made. Minimal content:
```toml
"$schema" = "https://conductor.build/schemas/settings.repo.schema.json"

[scripts]
setup = "uv sync && cd portal && bun install"
run = "uv run python -m server.main --port $CONDUCTOR_PORT"
run_mode = "concurrent"
```

---

### T8 — Ship (Evo-owned, not Claude Code)

Evo runs this autonomously after T7 passes:

1. Final full test run: `uv run pytest && cd portal && bun test && bun run build` — all green
2. Eval harness: `uv run scripts/eval.py` — 10/10 confirmed
3. Samuel completes 3 Research runs + 3 Teaching runs on real topics via the portal (acceptance criterion from spec — cannot skip)
4. After Samuel signs off: `git tag -a v0.3.0 -m "feat: Phase D — Agent Foundation, agent runtime, Research + Teaching agents, /agent primary interface"`
5. `git push origin v0.3.0`
6. Confirm GitHub release page shows v0.3.0

---

## Checkpoints summary

| After | Checkpoint | Owner |
|---|---|---|
| T2 | Tool wrappers confirmed as thin closures over v0.2.0 code — no retrieval rebuild | Evo |
| T4 | CLI dry-run on real topic — agent loop works, cost tracked, artifact in KB | Evo |
| T6 | Portal review + Samuel first live end-to-end run | Evo + Samuel |
| T7 | Eval 10/10, all tests green, CI passes | Evo |
| T8 | Samuel 3x Research + 3x Teaching, then tag | Samuel → Evo |

---

## What Claude Code must not do

- Do not rewrite `core/memory/retrieval.py` — tool wraps it, does not replace it
- Do not rewrite `core/llm/bedrock.py` — tool wraps it, does not replace it
- Do not modify migrations 001 or 002 — forward-only rule
- Do not extract `artifacts` schema to 001_initial.sql — that's Phase H work
- Do not add framework deps (smolagents, pydantic-ai, LangGraph) — custom loop is the decision
- Do not add WebSocket — polling is Phase D, WebSocket is Phase D.1 or later
- Do not put `agents/` at project root — they go in `core/agents/`
- Do not leave `server.py` at repo root after Phase D — restructure to `server/` is required
- Do not create phantom files — only create files the phase actually needs
- Do not commit with phase-tracking messages ("T1 complete", "Phase D done") — describe what changed
- Do not make web API calls outside of the LLM provider (Bedrock) — no telemetry, no analytics

---

## Post-Phase-D backlog (logged, not actioned yet)

**cost_usd always 0.0** (T4 audit, Samuel 2026-06-08) — `generate.py` hardcodes `cost_usd: 0.0`. Bedrock's `invoke_model` response includes `usage.inputTokens` and `usage.outputTokens`. Wire through `provider.chat()` return value → `generate` tool → `call_tool` accumulator in Phase G (or earlier if cost display is needed in portal). Action: add `usage` dict to `ChatResponse`; update `generate` tool to read it; accumulate in `loop.py`.

**Migration not auto-applied** (T4 audit, Samuel 2026-06-08) — `open_db()` doesn't run pending migrations. Fixed in T5 (Part 5, Fix 2). Tracking here as resolved-in-T5.

**Phase E — Skill file YAML frontmatter** (T3 audit note, Samuel 2026-06-08)

`core/prompts/research_wiki.md` and `core/prompts/teach_me.md` are functional but lack YAML frontmatter. Agent platforms (Claude Code, Hermes, Cursor) use self-describing skill files with `name`, `description`, `version`, `metadata` front-matter. When Phase E portability work ships, `templates.py` should parse frontmatter + body separately. This is a one-task refactor — no architectural change.

Action when scheduled: add frontmatter to both skill files + update `templates.py` `_load()` to strip frontmatter before returning body.

---

## Key decisions summary

| Decision | Resolution | Rationale |
|---|---|---|
| Agent loop | Custom Python | Runtime is the product thesis; framework wrapper undermines AI Platform Engineering positioning |
| Teaching turns | Polling (2s interval) | WebSocket adds complexity for no local-tool benefit; earn it in Phase D.1 |
| Auto-chain default | On | Core loop is the product; opt-out is the exception |
| Tool wrappers | Functions with closures | Matches codebase style; cleaner imports; trivially mockable |
| Migration hygiene | Leave for Phase H | Portability work, zero current value, non-trivial DB risk |
