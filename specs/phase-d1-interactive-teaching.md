# EvoResearch v0.3.1 — Interactive Teaching Session

**Version:** 0.3.1
**Status:** Ready to build
**Scope:** 3 fixes + 1 feature (interactive teaching session)

---

## Context

v0.3.0 shipped the Teaching Agent in non-interactive mode (auto-advance 3 turns, fires and forgets).
The portal `/message` endpoint is a stub. There is no `teach-session.tsx` UI component.
This spec defines the full interactive teaching session for v0.3.1.

---

## Fix 1 — Iframe dark render (small)

**Root cause:** The Research Agent LLM output contains dark-themed CSS (`body { background: #1a1a1a; color: #e5e5e5; }` etc). The `ArtifactViewer` iframe sets `backgroundColor: "white"` on the container but the `srcDoc` HTML itself overrides it.

**Fix:** In `core/tools/ingest.py`, before saving `html_content` to disk, inject a style override at the top of `<head>`:

```python
LIGHT_OVERRIDE = (
    "<style>"
    "html,body{background:#fff!important;color:#111!important;}"
    "* {color-scheme: light!important;}"
    "</style>"
)
```

If `<head>` exists, insert after `<head>`. If no `<head>`, prepend.

Apply to ALL future artifact saves. Do NOT retroactively patch existing files (covered by Fix 2 migration if needed).

**Files:** `core/tools/ingest.py`
**Tests:** Add unit test: given dark-body HTML, injected HTML contains the override style.

---

## Fix 2 — Raw HTML in summaries (small)

**Root cause:** Some artifacts in the DB have raw HTML in their `summary` field (e.g. `` ```html <!DOCTYPE html>... ``). The `fb16b3b` strip fix only applies at agent write-time — existing rows in SQLite are already corrupted.

**Fix 2a — Agent-time (already fixed in fb16b3b, verify stays):**
`core/agents/research.py` strips HTML tags from `summary` before passing to the ingest tool.

**Fix 2b — One-time migration script:**
`scripts/fix_summaries.py` — reads all artifacts where `summary` contains `<` or ` ```html`, strips HTML/markdown fences, writes back via `UPDATE artifacts SET summary = ? WHERE id = ?`.

Logic:
1. `re.sub(r'<[^>]+>', '', summary)` — strip HTML tags
2. Strip ` ```html ` / ` ``` ` markdown fences
3. Collapse whitespace
4. Take first 300 chars if result is still too long (truncate at sentence boundary)

Run once. Safe to re-run (idempotent).

**Files:** `scripts/fix_summaries.py` (new)
**Tests:** Unit test for the strip function (no DB connection needed).

---

## Feature — Interactive Teaching Session (medium)

### Architecture overview

The current teaching agent runs to completion synchronously. Interactive mode requires:

1. Teaching agent **pauses** after each layer, awaiting user response
2. Status: `paused_awaiting_input` (new state in `agent_runs`)
3. User sends `POST /api/agent/{run_id}/message` with their response
4. Server resumes the teaching session from where it paused
5. Portal polls `GET /api/agent/{run_id}` every 2s and renders the latest turn

### State machine

```
running → paused_awaiting_input → running → ... → complete
                                           ↘ failed
```

New status value: `"paused_awaiting_input"` (add to `agent_runs` check constraint or just use it as a valid string)

### DB change

Add `session_log` column to `agent_runs` for persisting multi-turn state between `/message` calls:

```sql
ALTER TABLE agent_runs ADD COLUMN session_log TEXT;  -- JSON array of {role, content}
```

New migration: `scripts/migrations/004_phase_d1.sql`

### Backend changes

**`core/runtime/contracts.py`:**
- Add `"paused_awaiting_input"` as valid status literal
- `AgentRun` already has `tool_calls` — add `session_log: list[dict] | None = None`

**`core/agents/teaching.py`:**
- Add `run_teaching_turn(run_id, user_message, session_log, call_tool)` function
- First call: `user_message=None` → runs opening layer, returns after layer 1, status = `paused_awaiting_input`, `session_log` saved
- Subsequent calls: `user_message` fed into `TEACH_LAYER`, runs next layer, pauses again
- After connections + checklist: status = `complete`

**`core/governance/audit.py`:**
- Add `pause_run(db, run_id, session_log)` → sets status = `paused_awaiting_input`, serializes session_log
- Add `resume_run(db, run_id)` → sets status = `running`
- Update `get_run` to include `session_log` in return dict

**`server/routes/agent.py` — `POST /{run_id}/message`:**
- Remove stub response
- Load run from DB, check status == `paused_awaiting_input`
- Deserialize `session_log` from DB
- Call `run_teaching_turn(run_id, content, session_log, call_tool)` 
- Return `{reply, status, session_log_length}`

**`server/routes/agent.py` — `POST /api/agent` (research dispatch):**
- Keep existing synchronous fire-and-forget for Research
- Teaching dispatch: run opening layer only, pause, return `run_id` + status `paused_awaiting_input`

### Portal changes

**`portal/components/teach-session.tsx` (new):**
- Receives `run_id` and initial `reply` from dispatch
- Polls `GET /api/agent/{run_id}` every 2s while status == `running`
- Renders conversation as a thread: assistant turns + user input box
- Shows current turn as typing indicator while `running`
- Disables input while `running`, enables when `paused_awaiting_input`
- On submit: `POST /api/agent/{run_id}/message` → append reply, continue

**`portal/components/run-status.tsx`:**
- If `teach_run.status == "paused_awaiting_input"` → render `<TeachSession runId={teach_run.id} initialReply={...} />`
- If `teach_run.status == "complete"` → show existing checklist link

**`portal/lib/agent-client.ts`:**
- `sendMessage(runId, content)` — already exists, verify return type matches new API shape

### Turn flow (from user's perspective)

1. User hits "Run" (Research + auto-teach)
2. Research runs synchronously → complete
3. Teaching opens → returns opening question → status `paused_awaiting_input`
4. Portal renders `TeachSession` with opening question + input box
5. User types response, submits
6. Portal calls `/message`, waits, displays next layer
7. Repeat until checklist generated
8. Portal shows "View checklist →" link

### Constraints (carry over from v0.3.0 spec)

- **Polling, not WebSocket** — 2s `setInterval`, cancel on `complete`/`failed`/unmount
- **No new framework deps** — custom loop, no smolagents, no LangGraph
- **Session log in DB** — `TEXT` column, JSON-serialized, max ~50KB per session
- **`EVO_TEACH_MAX_TURNS` still respected** — cap at env var value, default 20

---

## Delivery checklist

- [ ] `scripts/migrations/004_phase_d1.sql` — `session_log` column
- [ ] `scripts/fix_summaries.py` — one-time retrofix
- [ ] `core/tools/ingest.py` — light style injection
- [ ] `core/governance/audit.py` — `pause_run`, `resume_run`, updated `get_run`
- [ ] `core/runtime/contracts.py` — `paused_awaiting_input` status
- [ ] `core/agents/teaching.py` — `run_teaching_turn()`, pause/resume logic
- [ ] `server/routes/agent.py` — real `/message` handler
- [ ] `portal/components/teach-session.tsx` — new component
- [ ] `portal/components/run-status.tsx` — wire TeachSession
- [ ] Tests: unit (audit, teaching turn, ingest style inject, summary strip) + portal (TeachSession component, /message proxy)
- [ ] CHANGELOG.md v0.3.1 section
- [ ] Git tag v0.3.1

## Success criteria

- [ ] Research artifact renders white (not black) in KB viewer
- [ ] KB card summaries show plain text (not raw HTML)
- [ ] Teaching run in portal: opening question appears, input box active, user can respond, session advances to checklist
- [ ] Checklist artifact auto-links after session completes
- [ ] All existing tests still pass (137 Python + 41 portal)
- [ ] New tests: ≥ 15 new assertions covering the above
