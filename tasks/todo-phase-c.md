# Phase C — Todo (v0.2.0)

> Status: READY TO START
> Plan: [tasks/plan-phase-c.md](./plan-phase-c.md)
> Spec: [specs/phase-c-rag.md](../specs/phase-c-rag.md)

---

- [ ] **T1** — Migration + schema: `scripts/migrations/002_phase_c.sql`, `scripts/migrate.py`, `tests/test_migrations.py`, new deps in `pyproject.toml`
- [ ] **T2** — Chunker: `lib/chunker.py`, `tests/fixtures/sample_artifact.html`, `tests/test_chunker.py` — *checkpoint: Evo reviews chunker output before embedding*
- [ ] **T3** — Ingest integration: wire chunker into `scripts/ingest.py`, extract `lib/db.py`
- [ ] **T4** — Embed pipeline: `scripts/embed.py`, `lib/provider.py`, `tests/test_embed.py`, `tests/test_provider.py`
- [ ] **T5** — Retrieval: `lib/retrieve.py`, `lib/prompts.py`, `tests/fixtures/eval_questions.json`, `tests/test_retrieve.py` — *checkpoint: Evo reviews eval set before UI*
- [ ] **T6** — Chat API: `portal/app/api/chat/route.ts`, `portal/lib/chat-client.ts`, `portal/__tests__/api/chat.test.ts`
- [ ] **T7** — Chat UI: `/chat` route, `chat-panel.tsx`, `chat-message.tsx`, `citation-badge.tsx`, nav link — *checkpoint: Evo end-to-end review + Samuel test drive*
- [ ] **T8** — Eval + hardening: `tests/test_eval.py`, CI update, `CHANGELOG.md`, `CLAUDE.md`, `README.md`
- [ ] **T9** — Tag + ship (Evo-owned): full test run, 3 sessions by Samuel, `v0.2.0` tag, push
