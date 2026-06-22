# Evo Migration Plan

## Phase 1: KB Restructure

### Vault changes (manual — do not execute)

- [ ] Rename folder `~/…/SamuelOS/Knowledge/Research/` → `~/…/SamuelOS/Knowledge/KB/`
- [ ] Move `~/…/SamuelOS/Knowledge/teach-me-grpc-checklist.md` → `~/…/SamuelOS/Knowledge/KB/teach-me-grpc-checklist.md`
- [ ] Verify `manifest.db`, `html/`, `summaries/` are intact inside the new `KB/` folder

### Code changes

#### `core/memory/db.py`

- [ ] Line 16: `/ "Research"` → `/ "KB"`

#### `scripts/ingest.py`

- [ ] Line 27: `/ "Research"` → `/ "KB"`

#### `scripts/migrate.py`

- [ ] Line 20: `/ "Samuel's Vault/SamuelOS/Knowledge/Research"` → `/ "Samuel's Vault/SamuelOS/Knowledge/KB"`

#### `portal/lib/path-guard.ts`

- [ ] Line 16: `"Research"` → `"KB"`

#### `server/routes/agent.py`

- [ ] Line 217: `/ "Knowledge" / "Research"` → `/ "Knowledge" / "KB"`

#### `CLAUDE.md`

- [ ] Line 23: `Knowledge/Research/` → `Knowledge/KB/`

#### `README.md`

- [ ] Line 78: `Knowledge/Research/` → `Knowledge/KB/`

#### `CHANGELOG.md`

- [ ] No change needed — historical record (describes what was true at v0.1.0)

---

## Phase 2: Project Rename

### Rename: `evo-research` → `evo`
### Rename: `EvoResearch` → `Evo`

---

### Documentation files

#### `README.md`

- [ ] Line 1: `# EvoResearch` → `# Evo`
- [ ] Line 5: "EvoResearch is an agent-first…" → "Evo is an agent-first…"
- [ ] Line 9: "EvoResearch follows the…" → "Evo follows the…"
- [ ] Line 84: `EVO_RESEARCH_STORE=/path/to/store` → `EVO_STORE=/path/to/store`

#### `VISION.md`

- [ ] Line 1: `# EvoResearch — Product Vision` → `# Evo — Product Vision`
- [ ] Line 75: "EvoResearch is built as an…" → "Evo is built as an…"
- [ ] Line 132: "EvoResearch's architecture follows…" → "Evo's architecture follows…"
- [ ] Line 134: "EvoResearch's component map:" → "Evo's component map:"
- [ ] Line 136: `| Harness component | EvoResearch implementation |` → `| Harness component | Evo implementation |`
- [ ] Line 147: "…is EvoResearch's specific…" → "…is Evo's specific…"
- [ ] Line 198: "EvoResearch is the missing memory layer." → "Evo is the missing memory layer."
- [ ] Line 219: '…EvoResearch is "Cursor for everything you learn."' → '…Evo is "Cursor for everything you learn."'
- [ ] Line 221: "EvoResearch builds your understanding." → "Evo builds your understanding."

#### `ROADMAP.md`

- [ ] Line 3: "EvoResearch evolves from…" → "Evo evolves from…"

#### `CHANGELOG.md`

- [ ] Line 3: "All notable changes to EvoResearch…" → "All notable changes to Evo…"
- [ ] Line 143: `EVO_RESEARCH_STORE` → `EVO_STORE`
- [ ] Line 160: `github.com/samueldanso/evo-research` → `github.com/samueldanso/evo` (all 5 link lines 160-164)

#### `CAPABILITIES.md`

- [ ] Line 3: "What EvoResearch is, in platform terms." → "What Evo is, in platform terms."

#### `CLAUDE.md`

- [ ] Line 1: `# EvoResearch — Project Context` → `# Evo — Project Context`
- [ ] Line 19: "EvoResearch is built as an agent platform product…" → "Evo is built as an agent platform product…"
- [ ] Line 84: `EVO_RESEARCH_STORE=/path/to/store` (README command example) — update
- [ ] Line 91: `Path.home()` or `EVO_RESEARCH_STORE` → `Path.home()` or `EVO_STORE`

---

### Python source files

#### `pyproject.toml`

- [ ] Line 2: `name = "evo-research"` → `name = "evo"`

#### `core/__init__.py`

- [ ] Line 1: `"""EvoResearch core — platform harness primitives."""` → `"""Evo core — platform harness primitives."""`

#### `core/memory/db.py`

- [ ] Line 1: `"""Shared database utilities for EvoResearch."""` → `"""Shared database utilities for Evo."""`
- [ ] Line 21: `os.environ.get("EVO_RESEARCH_STORE")` → `os.environ.get("EVO_STORE")`

#### `core/prompts/templates.py`

- [ ] Line 18: `"You are the Research Agent for EvoResearch…"` → `"You are the Research Agent for Evo…"`
- [ ] Line 39: `"You are the Teaching Agent for EvoResearch…"` → `"You are the Teaching Agent for Evo…"`

#### `core/runtime/dispatcher.py`

- [ ] Line 37: `os.environ.get("EVO_RESEARCH_STORE",…)` → `os.environ.get("EVO_STORE",…)`

#### `server/__init__.py`

- [ ] Line 1: `"""EvoResearch FastAPI server — agent + chat endpoints."""` → `"""Evo FastAPI server — agent + chat endpoints."""`

#### `server/config.py`

- [ ] Line 9: `EVO_RESEARCH_STORE = os.environ.get("EVO_RESEARCH_STORE")` → `EVO_STORE = os.environ.get("EVO_STORE")`

#### `server/routes/agent.py`

- [ ] Line 215: `"EVO_RESEARCH_STORE"` → `"EVO_STORE"`

#### `scripts/ingest.py`

- [ ] Line 2: `"""EvoResearch ingest CLI…"""` → `"""Evo ingest CLI…"""`
- [ ] Line 98: `os.environ.get("EVO_RESEARCH_STORE")` → `os.environ.get("EVO_STORE")`
- [ ] Line 281: `description="EvoResearch artifact ingest…"` → `description="Evo artifact ingest…"`

#### `scripts/embed.py`

- [ ] Line 2: `"""EvoResearch embed pipeline…"""` → `"""Evo embed pipeline…"""`
- [ ] Line 119: `description="EvoResearch embedding pipeline"` → `description="Evo embedding pipeline"`

#### `scripts/migrate.py`

- [ ] Line 1: `"""…forward-only DB migration runner for EvoResearch."""` → `"""…forward-only DB migration runner for Evo."""`
- [ ] Line 25: `os.environ.get("EVO_RESEARCH_STORE")` → `os.environ.get("EVO_STORE")`
- [ ] Line 115: `description="EvoResearch DB migration runner"` → `description="Evo DB migration runner"`

#### `scripts/agent.py`

- [ ] Line 2: `"""CLI dispatch for EvoResearch agents."""` → `"""CLI dispatch for Evo agents."""`
- [ ] Line 25: `description="EvoResearch agent CLI"` → `description="Evo agent CLI"`

#### `scripts/eval.py`

- [ ] Line 84: `"EvoResearch Phase C — Retrieval Smoke Test"` → `"Evo Phase C — Retrieval Smoke Test"`
- [ ] Line 111: `description="EvoResearch retrieval smoke test"` → `description="Evo retrieval smoke test"`

---

### Tests

#### `tests/test_ingest.py`

- [ ] Lines 69, 295, 307, 318, 331, 341, 358, 370, 385, 407, 417, 427, 435, 443: all `"EVO_RESEARCH_STORE"` → `"EVO_STORE"`

#### `tests/test_agents.py`

- [ ] Lines 116, 126, 149, 159: `"EVO_RESEARCH_STORE"` → `"EVO_STORE"`

---

### Portal

#### `portal/app/layout.tsx`

- [ ] Line 17: `title: "EvoResearch"` → `title: "Evo"`
- [ ] Line 31: `EvoResearch` (nav brand text) → `Evo`

#### `portal/app/page.tsx`

- [ ] Line 9: `<h1…>EvoResearch</h1>` → `<h1…>Evo</h1>`

#### `portal/lib/path-guard.ts`

- [ ] Line 6: `process.env.EVO_RESEARCH_STORE` → `process.env.EVO_STORE`

#### `portal/__tests__/api/artifacts-slug-html.test.ts`

- [ ] Line 42: `process.env.EVO_RESEARCH_STORE` → `process.env.EVO_STORE`
- [ ] Line 50: `delete process.env.EVO_RESEARCH_STORE` → `delete process.env.EVO_STORE`

---

### CI / GitHub

#### `.github/workflows/ci.yml`

- [ ] Line 33: `EVO_RESEARCH_STORE: /tmp/evo-test-store` → `EVO_STORE: /tmp/evo-test-store`
- [ ] Line 38: `EVO_RESEARCH_STORE: /tmp/evo-test-store` → `EVO_STORE: /tmp/evo-test-store`

---

### `.claude/` (project commands)

#### `.claude/commands/ingest.md`

- [ ] Line 3: "…into the EvoResearch vault" → "…into the Evo vault"

---

### Specs / Tasks (historical docs — update for consistency)

#### `specs/phase-c-rag.md`

- [ ] Line 237: "You are EvoResearch, a research assistant…" → "You are Evo, a research assistant…"

#### `specs/phase-d-agent-foundation.md`

- [ ] Line 7: "…core architectural primitive of EvoResearch." → "…core architectural primitive of Evo."

#### `specs/phase-d1-interactive-teaching.md`

- [ ] Line 1: `# EvoResearch v0.3.1` → `# Evo v0.3.1`

#### `tasks/plan-phase-d.md`

- [ ] Line 15: "EvoResearch is being built as an…" → "Evo is being built as an…"
- [ ] Line 337: `EVO_RESEARCH_STORE` → `EVO_STORE`
- [ ] Line 475: `EVO_RESEARCH_STORE` → `EVO_STORE`

---

### GitHub remote (out of scope — manual)

- [ ] Rename GitHub repository `samueldanso/evo-research` → `samueldanso/evo`
- [ ] Update local git remote: `git remote set-url origin git@github.com:samueldanso/evo.git`

---

## Execution order

1. **Phase 1 first** — rename vault folder, update all `Research` → `KB` path references, run tests
2. **Phase 2 second** — rename project, update all `EvoResearch`/`evo-research`/`EVO_RESEARCH_STORE` references, run tests
3. Tag + push after each phase passes `uv run pytest && cd portal && bun test && bun run build`
