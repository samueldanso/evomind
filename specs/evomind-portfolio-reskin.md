# EvoMind Portfolio Reskin

> Rebrand and reskin Evo into EvoMind — a polished, demo-ready AI knowledge base for Samuel's portfolio. No new backend features. Portal redesign only.

**Date:** 2026-09-02
**Status:** Approved
**Goal:** A presentable portfolio project that demonstrates AI/RAG/agent engineering depth to recruiters and hiring managers for AI Engineer, Agent Engineer, Applied AI, LLM Engineer, and Gen AI roles.

---

## 1. Context & Motivation

Evo shipped through Phase D (v0.3.1) with a working Python backend: hybrid retrieval (vector + FTS5), research agents, embedding pipeline, eval harness (10/10), agent audit log, and ingest pipeline. The portal looks like a developer tool — functional but not portfolio-ready.

EvoMind is a hackathon project (built with a friend) with the same concept — AI-powered knowledge base — but with a polished dark UI, clear information hierarchy, and demo-ready visual craft.

**The play:** Port EvoMind's design language onto Evo's backend. The visitor sees a polished product. The interviewer reads the Python backend and sees real AI platform engineering.

**What this is NOT:**
- Not a product for customers
- Not a feature expansion
- Not a backend rewrite
- Not continuing the Evo roadmap (Phases E-J are shelved)

---

## 2. Brand Identity

- **Name:** EvoMind
- **Tagline:** "The goal isn't to remember everything. It's to never lose what matters."
- **Portfolio pitch:** AI-powered personal knowledge base with hybrid RAG retrieval, autonomous research agents, and a compounding knowledge graph.

---

## 3. Design System

Ported from the EvoMind hackathon project's `globals.css` (830-line design system).

### Palette (dark-first)

| Token | Value | Usage |
|-------|-------|-------|
| `--bg-base` | `#09090b` | Page background |
| `--surface-1` | `#0c0c0e` | Card backgrounds |
| `--surface-2` | `#111113` | Elevated cards |
| `--surface-3` | `#18181b` | Active/hover states |
| `--ink` | `#f5f5f4` | Primary text |
| `--ink-secondary` | `rgba(245,245,244,0.7)` | Secondary text |
| `--accent` | `#d4a574` | Warm gold — focus, highlights, CTAs |
| `--border` | `rgba(255,255,255,0.08)` | Default borders |
| `--border-strong` | `rgba(255,255,255,0.15)` | Emphasis borders |

### Type-colored badges

| Type | Color | Hex |
|------|-------|-----|
| Concept | Lavender | `#C7B8FF` |
| Person | Green | `#9BDCAA` |
| Place | Gold | `#F4C77B` |
| Event | Coral | `#F49B9B` |
| Tool | Cyan | `#7BD0E8` |
| Organization | Periwinkle | `#B4B0F0` |

### Typography

- **Primary:** Inter (body, UI) — `font-feature-settings: "cv02", "cv03", "cv04", "cv11"`
- **Accent:** Instrument Serif (lead paragraphs, blockquotes, hero italic)
- **Mono:** JetBrains Mono (code blocks, metadata, scores)
- **Scale:** Custom tokens from 10px (`--fs-micro`) to 56px (`--fs-h1`)

### Component patterns

- **Cards:** `.app-card` — subtle border, bg transition on hover, 1px upward translate
- **Buttons:** Pill-shaped (`border-radius: 9999px`). Primary = white bg/dark text. Ghost = transparent/bordered.
- **Badges:** Small pill with type-specific background color at low opacity, colored text
- **Layout:** Centered content columns, max-widths per page context

---

## 4. Pages

### 4.1 `/` — Landing Page

**Purpose:** First impression. Sell the project in 5 seconds.

**Structure:**
- Hero section: animated tagline (WordsPullUp or FadeUp from EvoMind), one-line description, two CTAs ("Explore Wiki" → `/wiki`, "Ask a Question" → `/search`)
- Feature cards section (3-4 cards):
  - **Hybrid RAG Retrieval** — Vector + FTS5 search with score-based merge
  - **Research Agents** — Autonomous topic research with structured note generation
  - **Embedding Pipeline** — Cohere Embed v4, batched with backoff, 1024-dim vectors
  - **Eval Harness** — 10-question retrieval quality gate, currently 10/10
- Brief architecture blurb or tech stack badges at the bottom

**Data:** None. Static page.

### 4.2 `/wiki` — Wiki Browser

**Purpose:** Browse all research artifacts in the knowledge base.

**Structure:**
- Header: page count, search input (FTS5, 300ms debounce)
- Type filter chips (concept, person, tool, etc.) — client-side filtering
- Tag filter pills extracted from all artifacts
- Responsive grid (1/2/3 columns) of artifact cards
- Each card: title, date, truncated summary (150 chars), type badge, tag pills
- Card click → `/wiki/[slug]`
- Empty state for no results

**Data:**
- `GET /api/artifacts` — list all (existing route, no changes)
- `GET /api/search?q=` — FTS5 search (existing route, no changes)

### 4.3 `/wiki/[slug]` — Wiki Page Detail

**Purpose:** Read a single research artifact.

**Structure:**
- Breadcrumb: "Wiki → [Title]"
- Two-column desktop layout:
  - **Left (content):** Type badge, title, reading time, summary in Instrument Serif italic, rendered HTML content in sandboxed iframe (existing `artifact-viewer.tsx` pattern, restyled)
  - **Right (sidebar, sticky):** Metadata panel — date, tags, type, word count
- Single column on mobile (sidebar collapses below content)
- "Back to Wiki" link

**Data:**
- `GET /api/artifacts/[slug]` — metadata (existing route)
- `GET /api/artifacts/[slug]/html` — HTML content (existing route)

### 4.4 `/search` — Ask AI

**Purpose:** THE RAG demo. Ask questions, get cited answers from the knowledge base.

**Structure:**
- Two tabs: "Ask AI" and "Search"
- **Ask AI tab:**
  - Query input with submit button
  - Answer display (prose, Instrument Serif for readability) — single-turn, not streaming (Evo's `/chat` returns JSON, not SSE)
  - Source citations below answer: artifact title, match type badge (vector/FTS5/hybrid), relevance score, link to `/wiki/[slug]`
  - Loading state with animated indicator
  - Error state
- **Search tab:**
  - Instant keyword search input
  - Results as compact card list filtered client-side from all artifacts
- Query history in localStorage (nice-to-have, not required)

**Data:**
- Ask AI: `POST /api/chat` — proxy to Python FastAPI `/chat` (existing, fix hardcoded URL)
- Search: `GET /api/search?q=` — existing FTS5 route

---

## 5. Navigation

**Topbar:** Fixed/sticky, 52px height, glassy blur on scroll.
- **Left:** EvoMind logo/wordmark
- **Center:** `Wiki` | `Search`
- **Right:** GitHub repo link icon

Two nav items. Nothing else.

---

## 6. Portal Changes (Explicit)

### Files to DELETE
- `app/page.tsx` (agent form home) — replaced by landing
- `app/chat/page.tsx` — replaced by `/search`
- `app/runs/page.tsx` — cut
- `app/kb/page.tsx` — replaced by `/wiki`
- `app/api/agent/route.ts` — cut
- `app/api/agent/[run_id]/route.ts` — cut
- `app/api/agent/[run_id]/message/route.ts` — cut
- `components/agent-form.tsx` — cut
- `components/run-status.tsx` — cut
- `components/teach-session.tsx` — cut
- `components/run-history.tsx` — cut
- `lib/agent-client.ts` — cut

### Files to CREATE
- `app/page.tsx` — landing hero
- `app/wiki/page.tsx` — wiki browser
- `app/wiki/[slug]/page.tsx` — wiki detail
- `app/search/page.tsx` — dual-mode search/ask
- `app/globals.css` — rewritten with EvoMind design tokens
- `app/layout.tsx` — rewritten with new fonts, topbar, dark theme
- `components/topbar.tsx` — new navigation
- `components/wiki-card.tsx` — artifact card restyled
- `components/wiki-grid.tsx` — grid with filters
- `components/source-card.tsx` — citation card for search results
- `components/feature-card.tsx` — landing page feature cards

### Files to MODIFY
- `lib/chat.ts` — replace hardcoded `localhost:8765` with `EVO_SERVER_URL` env var
- `components/artifact-viewer.tsx` — restyle for dark theme (keep sandbox logic)

### Files UNTOUCHED
- `lib/db.ts`, `lib/types.ts`, `lib/path-guard.ts`, `lib/utils.ts`
- `app/api/search/route.ts`
- `app/api/artifacts/route.ts`, `app/api/artifacts/[slug]/route.ts`, `app/api/artifacts/[slug]/html/route.ts`

### Test files
- DELETE: `__tests__/api/agent.test.ts` and related agent test files (routes removed)
- KEEP: `__tests__/api/search.test.ts`, `__tests__/api/artifacts.test.ts`, `__tests__/lib/chat.test.ts`
- DELETE: `__tests__/components/teach-session.test.ts` (component removed)

---

## 7. Backend Changes

### Python backend: ZERO changes
- All `core/` code untouched
- All `server/` code untouched
- All `scripts/` untouched
- All 153 Python tests must still pass

### Portal backend (API routes):
- Delete agent proxy routes (`/api/agent/*`)
- Existing artifact + search routes stay
- Chat proxy route stays (URL fix only)

---

## 8. Project Root Changes

### README.md — Full rewrite
- Project name: EvoMind
- One-line description
- Screenshot(s) or architecture diagram
- "What it demonstrates" section: Hybrid RAG, Agent orchestration, Embedding pipeline, Eval harness, Local-first SQLite
- Tech stack table
- How to run (Python backend + portal)
- Architecture overview
- Link to portfolio site

### Branding updates
- `VISION.md`, `ROADMAP.md`, `CAPABILITIES.md`, `CHANGELOG.md` — update "Evo" references to "EvoMind" where visible. Keep the engineering content intact.
- `portal/app/layout.tsx` — metadata title/description → EvoMind

---

## 9. Demo Data

Use existing Evo corpus already ingested. No new data pipeline work. The wiki browser and search should show real research artifacts from previous ingestion runs.

---

## 10. Acceptance Criteria

- [ ] Landing page loads with hero, feature cards, CTAs
- [ ] `/wiki` shows all artifacts in dark-themed grid with type badges and search
- [ ] `/wiki/[slug]` renders artifact content in two-column layout
- [ ] `/search` "Ask AI" streams answers with source citations from the RAG pipeline
- [ ] `/search` "Search" tab does instant keyword filtering
- [ ] Navigation between all 4 pages works
- [ ] Dark theme applied consistently — no white flashes, no unstyled elements
- [ ] Mobile responsive (single column, stacked layouts)
- [ ] README rewritten for portfolio presentation
- [ ] All existing Python tests pass (153)
- [ ] Portal builds without errors (`bun run build`)
- [ ] Portal tests pass for remaining routes (`bun test`)

---

## 11. Out of Scope

- Authentication / user accounts
- Knowledge graph visualization
- Agent invocation UI
- Run history UI
- Teaching agent UI
- Ingest UI
- Diary, audit pages
- New Python features
- New database migrations
- Deployment (local demo only for now)
- Dark/light mode toggle (dark-only)
