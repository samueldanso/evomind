# EvoMind Portfolio Reskin — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reskin Evo's portal into EvoMind — a polished, dark-themed AI knowledge base portfolio piece.

**Architecture:** Replace portal's design system, delete agent/teaching UI, rebuild 4 pages (Landing, Wiki, Wiki Detail, Search) using EvoMind's dark design language. Keep all existing API routes and Python backend untouched.

**Tech Stack:** Next.js 16, React 19, Tailwind v4, shadcn/ui, Inter + Instrument Serif + JetBrains Mono, better-sqlite3 (readonly), Framer Motion (new dep)

## Global Constraints

- Zero Python backend changes — all 153 tests must still pass
- Portal must build cleanly (`bun run build`)
- Dark-only theme (no light mode, no toggle)
- All artifact/search API routes stay as-is
- `lib/db.ts`, `lib/types.ts`, `lib/path-guard.ts`, `lib/utils.ts` — untouched
- Use existing `@base-ui/react` shadcn primitives (Button, Card, Badge, Input)
- Commit after each task

---

### Task 1: Add Dependencies & Fonts

**Files:**
- Modify: `portal/package.json`
- Modify: `portal/app/layout.tsx`

**Interfaces:**
- Produces: `--font-sans` (Inter), `--font-serif` (Instrument Serif), `--font-mono` (JetBrains Mono) CSS variables available globally. `framer-motion` importable.

- [ ] **Step 1: Install framer-motion**

```bash
cd portal && bun add framer-motion
```

- [ ] **Step 2: Verify install**

```bash
cd portal && bun run build
```

Expected: Build succeeds (no code changes yet, just a new dep).

- [ ] **Step 3: Commit**

```bash
git add portal/package.json portal/bun.lock
git commit -m "feat(portal): add framer-motion dependency"
```

---

### Task 2: Replace Design System

**Files:**
- Rewrite: `portal/app/globals.css`
- Rewrite: `portal/app/layout.tsx`

**Interfaces:**
- Consumes: framer-motion from Task 1
- Produces: Full dark design system — CSS tokens, card/button/input primitives, typography utilities, wiki prose styles. Root layout with Inter font, dark body, simple topbar with `Wiki` and `Search` nav links plus GitHub icon.

- [ ] **Step 1: Replace globals.css with EvoMind design system**

Rewrite `portal/app/globals.css` with the dark palette, surface tokens, typography scale, card/button/input primitives, wiki prose styles, scrollbar styles, and animation keyframes. Key tokens:

```css
@import "tailwindcss";
@import "tw-animate-css";
@import "shadcn/tailwind.css";

@custom-variant dark (&:is(.dark *));

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --font-serif: 'Instrument Serif', Georgia, serif;
  /* ... rest of shadcn theme inline mappings (keep existing ones) ... */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-xl: 18px;
  --radius-2xl: 24px;
}

:root {
  /* Core palette — near-black dark theme */
  --background: #09090b;
  --foreground: #fafafa;
  --card: #0c0c0e;
  --card-foreground: #fafafa;
  --popover: #0c0c0e;
  --popover-foreground: #fafafa;
  --primary: #f5f5f4;
  --primary-foreground: #09090b;
  --secondary: #18181b;
  --secondary-foreground: #fafafa;
  --muted: #18181b;
  --muted-foreground: #71717a;
  --accent: #18181b;
  --accent-foreground: #fafafa;
  --destructive: #ef4444;
  --border: rgba(255, 255, 255, 0.06);
  --input: rgba(255, 255, 255, 0.08);
  --ring: rgba(255, 255, 255, 0.2);
  --radius: 12px;

  /* Semantic ink tokens */
  --ink: #f5f5f4;
  --ink-secondary: rgba(245, 245, 244, 0.7);
  --ink-tertiary: rgba(245, 245, 244, 0.5);
  --ink-muted: rgba(245, 245, 244, 0.35);
  --ink-faint: rgba(245, 245, 244, 0.15);

  /* Surfaces */
  --surface-0: #09090b;
  --surface-1: #0c0c0e;
  --surface-2: #111113;
  --surface-3: #18181b;
  --surface-elevated: #1c1c1f;

  /* Borders */
  --border-subtle: rgba(255, 255, 255, 0.04);
  --border-default: rgba(255, 255, 255, 0.06);
  --border-strong: rgba(255, 255, 255, 0.1);
  --border-emphasis: rgba(255, 255, 255, 0.15);

  /* Accent — warm gold */
  --accent-warm: #d4a574;
  --accent-warm-soft: rgba(212, 165, 116, 0.6);
  --accent-warm-faint: rgba(212, 165, 116, 0.15);
}
```

Include all the utility classes from the EvoMind reference:
- `.app-card` / `.surface-card` / `.surface-elevated` / `.surface-glass`
- `.btn-primary` / `.btn-secondary` / `.btn-ghost` (pill-shaped)
- `.input-field`
- `.wiki-prose` (full heading/paragraph/list/code/blockquote styles)
- `.kicker` / `.section-title` / `.font-serif-italic` / `.text-gradient`
- Scrollbar styles (6px, hidden by default)
- `.animate-fade-in` / `.animate-slide-up` keyframes
- `@layer base` with `font-feature-settings: "cv02", "cv03", "cv04", "cv11"` on body

Remove the `.dark {}` block entirely (dark-only, no light mode). Remove all sidebar CSS variables (no sidebar in this project). Keep the shadcn `@theme inline` mappings for `--color-*` so shadcn components still work.

- [ ] **Step 2: Rewrite layout.tsx**

Replace `portal/app/layout.tsx`:

```tsx
import type { Metadata, Viewport } from "next";
import Link from "next/link";
import { Inter, Instrument_Serif, JetBrains_Mono } from "next/font/google";
import { Github } from "lucide-react";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-sans",
});

const instrumentSerif = Instrument_Serif({
  weight: "400",
  subsets: ["latin"],
  display: "swap",
  variable: "--font-serif",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "EvoMind — AI-Powered Knowledge Base",
  description:
    "Personal knowledge base with hybrid RAG retrieval, autonomous research agents, and a compounding knowledge graph.",
};

export const viewport: Viewport = {
  themeColor: "#09090b",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${instrumentSerif.variable} ${jetbrainsMono.variable}`}
    >
      <body className="min-h-screen bg-[#09090b] text-[#f5f5f4] antialiased">
        <header
          className="sticky top-0 z-30 h-[52px] flex items-center px-5"
          style={{
            background: "rgba(9,9,11,0.88)",
            backdropFilter: "blur(16px)",
            WebkitBackdropFilter: "blur(16px)",
            borderBottom: "1px solid rgba(255,255,255,0.04)",
          }}
        >
          <div className="flex items-center gap-2">
            <Link href="/" className="flex items-center gap-2 hover:opacity-70 transition-opacity">
              <span className="text-[17px] font-medium text-[#f5f5f4]">N</span>
              <span className="hidden sm:inline text-[11px] font-medium tracking-[0.2em] uppercase text-[rgba(245,245,244,0.45)]">
                EvoMind
              </span>
            </Link>
          </div>

          <nav className="flex-1 flex items-center justify-center gap-1">
            <NavLink href="/wiki">Wiki</NavLink>
            <NavLink href="/search">Search</NavLink>
          </nav>

          <div className="flex items-center">
            <a
              href="https://github.com/samueldanso/evo"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded-lg text-[rgba(245,245,244,0.4)] hover:text-[#f5f5f4] hover:bg-[rgba(255,255,255,0.04)] transition-all"
              aria-label="View on GitHub"
            >
              <Github size={16} />
            </a>
          </div>
        </header>

        <main className="min-h-[calc(100vh-52px)]">{children}</main>
      </body>
    </html>
  );
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="px-3 py-1.5 rounded-lg text-[13px] font-medium text-[rgba(245,245,244,0.42)] hover:text-[#f5f5f4] hover:bg-[rgba(255,255,255,0.04)] transition-all"
    >
      {children}
    </Link>
  );
}
```

Note: The GitHub URL should be updated to the actual repo URL when known. The `NavLink` component does not have active state highlighting — it's a static portfolio piece, not a SPA with complex routing needs. If active states are desired later, add `usePathname()` and make the component a client component.

- [ ] **Step 3: Verify build**

```bash
cd portal && bun run build
```

Expected: Build succeeds. Pages may error at runtime (old pages reference deleted styles), but the build should complete since pages are server-rendered on demand.

- [ ] **Step 4: Commit**

```bash
git add portal/app/globals.css portal/app/layout.tsx
git commit -m "feat(portal): replace design system with EvoMind dark theme"
```

---

### Task 3: Delete Old Files & Fix Chat Client

**Files:**
- Delete: `portal/app/chat/page.tsx`
- Delete: `portal/app/runs/page.tsx`
- Delete: `portal/app/kb/page.tsx`
- Delete: `portal/app/artifacts/[slug]/page.tsx`
- Delete: `portal/app/api/agent/route.ts`
- Delete: `portal/app/api/agent/[run_id]/route.ts`
- Delete: `portal/app/api/agent/[run_id]/message/route.ts`
- Delete: `portal/components/agent-form.tsx`
- Delete: `portal/components/run-status.tsx`
- Delete: `portal/components/teach-session.tsx`
- Delete: `portal/components/run-history.tsx`
- Delete: `portal/lib/agent-client.ts`
- Delete: `portal/__tests__/api/agent.test.ts` (if exists)
- Delete: `portal/__tests__/components/teach-session.test.ts` (if exists)
- Modify: `portal/lib/chat.ts`

**Interfaces:**
- Produces: Clean file tree with only the files we're keeping. `chat()` function uses `EVO_SERVER_URL` env var instead of hardcoded localhost.

- [ ] **Step 1: Delete all old page and component files**

```bash
cd portal
rm -f app/chat/page.tsx
rmdir app/chat 2>/dev/null || true
rm -f app/runs/page.tsx
rmdir app/runs 2>/dev/null || true
rm -f app/kb/page.tsx
rmdir app/kb 2>/dev/null || true
rm -rf app/artifacts
rm -rf app/api/agent
rm -f components/agent-form.tsx
rm -f components/run-status.tsx
rm -f components/teach-session.tsx
rm -f components/run-history.tsx
rm -f lib/agent-client.ts
```

- [ ] **Step 2: Delete related test files**

```bash
cd portal
rm -f __tests__/api/agent.test.ts
rm -f __tests__/components/teach-session.test.ts
```

- [ ] **Step 3: Fix chat.ts — replace hardcoded URL**

Replace `portal/lib/chat.ts`:

```ts
export interface ChatRequest {
  query: string;
  limit?: number;
}

export interface ChatSource {
  slug: string;
  title: string;
  excerpt: string;
  score: number;
  match_type: string;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
}

const CHAT_SERVER_URL =
  typeof window === "undefined"
    ? `${process.env.EVO_SERVER_URL ?? "http://127.0.0.1:8765"}/chat`
    : "/api/chat";

export async function chat(query: string, limit = 5): Promise<ChatResponse> {
  const res = await fetch(CHAT_SERVER_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, limit }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.error ?? `Chat request failed with status ${res.status}`;
    throw new Error(message);
  }

  return res.json();
}
```

Note: The client-side path `/api/chat` requires a proxy route. We need to create `portal/app/api/chat/route.ts`:

```ts
import { NextRequest, NextResponse } from "next/server";

const SERVER_URL = process.env.EVO_SERVER_URL ?? "http://127.0.0.1:8765";

export async function POST(request: NextRequest) {
  const body = await request.json();

  const res = await fetch(`${SERVER_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const error = await res.text().catch(() => "Chat server error");
    return NextResponse.json({ error }, { status: res.status });
  }

  const data = await res.json();
  return NextResponse.json(data);
}
```

- [ ] **Step 4: Create placeholder pages so the app doesn't 404**

Create minimal placeholder files so the build doesn't break while we work on the real pages:

`portal/app/page.tsx`:
```tsx
export default function Home() {
  return <div className="p-10 text-center text-[rgba(245,245,244,0.5)]">Landing page — coming in Task 4</div>;
}
```

`portal/app/wiki/page.tsx`:
```tsx
export default function WikiPage() {
  return <div className="p-10 text-center text-[rgba(245,245,244,0.5)]">Wiki — coming in Task 5</div>;
}
```

`portal/app/wiki/[slug]/page.tsx`:
```tsx
export default function WikiDetailPage() {
  return <div className="p-10 text-center text-[rgba(245,245,244,0.5)]">Wiki detail — coming in Task 6</div>;
}
```

`portal/app/search/page.tsx`:
```tsx
export default function SearchPage() {
  return <div className="p-10 text-center text-[rgba(245,245,244,0.5)]">Search — coming in Task 7</div>;
}
```

- [ ] **Step 5: Verify build**

```bash
cd portal && bun run build
```

Expected: Build succeeds. Old routes are gone, placeholders exist.

- [ ] **Step 6: Run remaining tests**

```bash
cd portal && bun test
```

Expected: Agent and teach-session tests are deleted, so only search/artifacts/chat tests remain. Some may fail due to import changes — note failures for fixing.

- [ ] **Step 7: Commit**

```bash
git add -A portal/
git commit -m "refactor(portal): delete agent UI, fix chat client, add placeholders"
```

---

### Task 4: Landing Page

**Files:**
- Rewrite: `portal/app/page.tsx`

**Interfaces:**
- Consumes: Design system from Task 2 (`.btn-primary`, `.btn-secondary`, `.kicker`, `.section-title`, `.surface-card`, accent-warm tokens)
- Produces: Landing page at `/` with hero section and feature cards. Static page, no data fetching.

- [ ] **Step 1: Write the landing page**

Replace `portal/app/page.tsx`:

```tsx
import Link from "next/link";
import { ArrowRight, Search, Sparkles, Brain, Database, Shield } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-[#09090b]">
      {/* Hero */}
      <section className="relative min-h-[85vh] flex items-center justify-center px-6 overflow-hidden">
        {/* Warm glow */}
        <div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse at center, rgba(212,165,116,0.12) 0%, transparent 70%)",
          }}
        />

        <div className="relative z-10 max-w-3xl mx-auto text-center">
          <div className="mb-6">
            <span className="kicker inline-flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#d4a574]" />
              AI-Powered Knowledge Base
            </span>
          </div>

          <h1
            className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-medium tracking-tight text-balance"
            style={{ color: "#f5f5f4", lineHeight: 1.05, letterSpacing: "-0.03em" }}
          >
            Your research,
            <br />
            <span className="font-serif italic" style={{ color: "rgba(245,245,244,0.7)" }}>
              intelligently retrieved
            </span>
          </h1>

          <p
            className="mt-6 text-base sm:text-lg max-w-xl mx-auto text-balance"
            style={{ color: "rgba(245,245,244,0.5)", lineHeight: 1.6 }}
          >
            Ingest web research. Embed it into a hybrid vector + full-text search index.
            Ask questions and get cited answers grounded in your own knowledge base.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link href="/wiki" className="btn-primary group">
              <span>Explore the Wiki</span>
              <ArrowRight
                size={14}
                className="opacity-0 -ml-2 group-hover:opacity-100 group-hover:ml-0 transition-all duration-200"
              />
            </Link>
            <Link href="/search" className="btn-secondary">
              <Search size={14} />
              <span>Ask a Question</span>
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="px-6 py-20 border-t border-[rgba(255,255,255,0.04)]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <span className="kicker">Under the hood</span>
            <h2 className="section-title mt-2">Built with engineering depth</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
              {
                title: "Hybrid RAG Retrieval",
                desc: "Vector search (sqlite-vec, Cohere Embed v4) fused with FTS5 full-text search via score-based merge. Neither alone covers the question space — both together hit 10/10 on the eval harness.",
                Icon: Search,
              },
              {
                title: "Research Agents",
                desc: "Autonomous agents that retrieve existing context, generate structured notes via LLM, and ingest results back into the knowledge base. Tool-calling loop with allowlist enforcement and full audit log.",
                Icon: Brain,
              },
              {
                title: "Embedding Pipeline",
                desc: "Sentence-boundary chunking, Cohere Embed v4 at 1024 dimensions, batched processing with exponential backoff. Incremental and full rebuild modes.",
                Icon: Database,
              },
              {
                title: "Eval-Gated Quality",
                desc: "10-question retrieval quality harness gates every release. Currently 10/10. No agent change ships if retrieval regresses. The eval is the contract.",
                Icon: Shield,
              },
            ].map(({ title, desc, Icon }) => (
              <div key={title} className="surface-card p-6">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center mb-4"
                  style={{ background: "rgba(212,165,116,0.1)", color: "#d4a574" }}
                >
                  <Icon size={20} />
                </div>
                <h3 className="text-base font-medium mb-2" style={{ color: "#f5f5f4" }}>
                  {title}
                </h3>
                <p className="text-sm leading-relaxed" style={{ color: "rgba(245,245,244,0.5)" }}>
                  {desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Tech stack */}
      <section className="px-6 py-16 border-t border-[rgba(255,255,255,0.04)]">
        <div className="max-w-3xl mx-auto text-center">
          <span className="kicker">Stack</span>
          <div className="mt-4 flex flex-wrap items-center justify-center gap-3">
            {[
              "Python", "FastAPI", "SQLite", "sqlite-vec", "FTS5",
              "AWS Bedrock", "Claude Sonnet", "Cohere Embed v4",
              "Next.js 16", "React 19", "Tailwind v4",
            ].map((tech) => (
              <span
                key={tech}
                className="px-3 py-1.5 rounded-full text-xs font-medium"
                style={{
                  background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.08)",
                  color: "rgba(245,245,244,0.6)",
                }}
              >
                {tech}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Tagline */}
      <section className="px-6 py-20 border-t border-[rgba(255,255,255,0.04)]">
        <div className="max-w-3xl mx-auto text-center">
          <blockquote
            className="text-xl font-serif italic"
            style={{
              color: "rgba(245,245,244,0.55)",
            }}
          >
            &ldquo;The goal isn&apos;t to remember everything. It&apos;s to never lose what matters.&rdquo;
          </blockquote>
        </div>
      </section>
    </div>
  );
}
```

- [ ] **Step 2: Verify build and visual check**

```bash
cd portal && bun run build && bun dev
```

Open `http://localhost:3000` — confirm hero renders with warm gold glow, feature cards below, tech stack pills, tagline.

- [ ] **Step 3: Commit**

```bash
git add portal/app/page.tsx
git commit -m "feat(portal): add EvoMind landing page with hero and feature cards"
```

---

### Task 5: Wiki Browser Page

**Files:**
- Rewrite: `portal/app/wiki/page.tsx`
- Rewrite: `portal/components/artifact-card.tsx` → rename to `portal/components/wiki-card.tsx`
- Rewrite: `portal/components/artifact-grid.tsx` → rename to `portal/components/wiki-grid.tsx`

**Interfaces:**
- Consumes: `getDb()` from `lib/db.ts`, `Artifact` from `lib/types.ts`, `parseTags()` from `lib/utils.ts`, `/api/search` route (unchanged), `.app-card` / `.kicker` / `.section-title` from globals.css
- Produces: `/wiki` page with dark-themed grid, search, tag filters

- [ ] **Step 1: Create wiki-card.tsx**

Create `portal/components/wiki-card.tsx`:

```tsx
import Link from "next/link";
import type { Artifact } from "@/lib/types";
import { parseTags } from "@/lib/utils";

const TYPE_COLORS: Record<string, string> = {
  concept: "#C7B8FF",
  person: "#9BDCAA",
  place: "#F4C77B",
  event: "#F49B9B",
  tool: "#7BD0E8",
  organization: "#B4B0F0",
};

function TypeBadge({ type }: { type: string }) {
  const color = TYPE_COLORS[type.toLowerCase()] ?? "rgba(245,245,244,0.4)";
  return (
    <span
      className="inline-block px-2 py-0.5 rounded-full text-[10px] font-medium uppercase tracking-wider"
      style={{ background: `${color}15`, color }}
    >
      {type}
    </span>
  );
}

export function WikiCard({ artifact }: { artifact: Artifact }) {
  const tags = parseTags(artifact.tags);
  const summary = artifact.summary ?? "";
  const excerpt = summary.length > 120 ? `${summary.slice(0, 120)}…` : summary;
  const date = artifact.created_at.slice(0, 10);

  // Infer type from first tag, or default to "research"
  const type = tags[0] ?? "research";

  return (
    <Link href={`/wiki/${artifact.slug}`} className="block h-full">
      <article className="app-card h-full group">
        <TypeBadge type={type} />
        <h3
          className="text-base font-medium mt-3 mb-2 group-hover:text-[#f5f5f4] transition-colors duration-150 line-clamp-1"
          style={{ color: "rgba(245,245,244,0.9)" }}
        >
          {artifact.title}
        </h3>
        <p
          className="text-sm leading-relaxed line-clamp-2"
          style={{ color: "rgba(245,245,244,0.4)" }}
        >
          {excerpt}
        </p>
        <div className="flex items-center gap-2 mt-4">
          <span className="text-xs" style={{ color: "rgba(245,245,244,0.25)" }}>
            {date}
          </span>
          {tags.length > 1 &&
            tags.slice(1, 3).map((tag) => (
              <span
                key={tag}
                className="text-[10px] px-1.5 py-0.5 rounded"
                style={{
                  background: "rgba(255,255,255,0.04)",
                  color: "rgba(245,245,244,0.35)",
                }}
              >
                {tag}
              </span>
            ))}
        </div>
      </article>
    </Link>
  );
}
```

- [ ] **Step 2: Create wiki-grid.tsx**

Create `portal/components/wiki-grid.tsx`:

```tsx
"use client";

import { useEffect, useRef, useState } from "react";
import { Search } from "lucide-react";
import { WikiCard } from "@/components/wiki-card";
import type { Artifact } from "@/lib/types";
import { parseTags } from "@/lib/utils";

function uniqueTags(artifacts: Artifact[]): string[] {
  const seen = new Set<string>();
  for (const a of artifacts) {
    for (const tag of parseTags(a.tags)) {
      seen.add(tag);
    }
  }
  return Array.from(seen).sort();
}

export function WikiGrid({ artifacts }: { artifacts: Artifact[] }) {
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Artifact[] | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    abortRef.current?.abort();

    const q = searchQuery.trim();
    if (!q) {
      setSearchResults(null);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      const controller = new AbortController();
      abortRef.current = controller;
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`, {
          signal: controller.signal,
        });
        if (!res.ok) {
          setSearchResults([]);
          return;
        }
        const data = (await res.json()) as Artifact[];
        setSearchResults(data);
      } catch (err) {
        if (err instanceof Error && err.name === "AbortError") return;
        setSearchResults([]);
      }
    }, 300);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      abortRef.current?.abort();
    };
  }, [searchQuery]);

  const isSearchActive = searchResults !== null;
  const baseList = isSearchActive ? searchResults : artifacts;
  const allTags = uniqueTags(artifacts);

  function toggleTag(tag: string) {
    setSelectedTags((prev) => {
      const next = new Set(prev);
      if (next.has(tag)) next.delete(tag);
      else next.add(tag);
      return next;
    });
  }

  const displayed =
    !isSearchActive && selectedTags.size > 0
      ? baseList.filter((a) => parseTags(a.tags).some((tag) => selectedTags.has(tag)))
      : baseList;

  return (
    <div className="flex flex-col gap-6">
      {/* Search */}
      <div className="relative max-w-md">
        <Search
          size={16}
          className="absolute left-4 top-1/2 -translate-y-1/2"
          style={{ color: "rgba(245,245,244,0.3)" }}
        />
        <input
          type="text"
          placeholder="Search research…"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="input-field pl-11"
        />
      </div>

      {/* Tag filters */}
      {!isSearchActive && allTags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {allTags.map((tag) => {
            const active = selectedTags.has(tag);
            return (
              <button
                key={tag}
                type="button"
                onClick={() => toggleTag(tag)}
                className="px-3 py-1 rounded-full text-xs font-medium transition-all"
                style={{
                  background: active ? "rgba(212,165,116,0.15)" : "rgba(255,255,255,0.04)",
                  border: `1px solid ${active ? "rgba(212,165,116,0.3)" : "rgba(255,255,255,0.08)"}`,
                  color: active ? "#d4a574" : "rgba(245,245,244,0.5)",
                }}
              >
                {tag}
              </button>
            );
          })}
          {selectedTags.size > 0 && (
            <button
              type="button"
              onClick={() => setSelectedTags(new Set())}
              className="px-3 py-1 rounded-full text-xs font-medium text-[rgba(245,245,244,0.35)] hover:text-[rgba(245,245,244,0.6)] transition-colors"
            >
              Clear
            </button>
          )}
        </div>
      )}

      {/* Grid */}
      {displayed.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <p className="text-sm" style={{ color: "rgba(245,245,244,0.4)" }}>
            {isSearchActive
              ? `No results for "${searchQuery.trim()}".`
              : artifacts.length === 0
                ? "No research artifacts yet."
                : "No artifacts match the selected tags."}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {displayed.map((artifact) => (
            <WikiCard key={artifact.id} artifact={artifact} />
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Rewrite wiki page**

Replace `portal/app/wiki/page.tsx`:

```tsx
import { WikiGrid } from "@/components/wiki-grid";
import { getDb, resetDb } from "@/lib/db";
import type { Artifact } from "@/lib/types";

function fetchArtifacts(): Artifact[] {
  try {
    const db = getDb();
    return db.prepare("SELECT * FROM artifacts ORDER BY created_at DESC").all() as Artifact[];
  } catch (err) {
    resetDb();
    console.error("[wiki] failed to load artifacts:", err);
    return [];
  }
}

export default async function WikiPage() {
  const artifacts = fetchArtifacts();

  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-6xl px-6 py-12">
        <header className="mb-10">
          <span className="kicker">{artifacts.length} artifacts</span>
          <h1 className="section-title mt-2">Knowledge Base</h1>
          <p className="mt-2 text-sm" style={{ color: "rgba(245,245,244,0.45)" }}>
            Research artifacts built by agents and ingested from web sources.
          </p>
        </header>
        <WikiGrid artifacts={artifacts} />
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Delete old card/grid files**

```bash
cd portal
rm -f components/artifact-card.tsx
rm -f components/artifact-grid.tsx
```

- [ ] **Step 5: Verify build and visual check**

```bash
cd portal && bun run build && bun dev
```

Open `http://localhost:3000/wiki` — confirm dark grid with cards, search input, tag filter chips.

- [ ] **Step 6: Commit**

```bash
git add -A portal/
git commit -m "feat(portal): add wiki browser page with dark-themed grid and filters"
```

---

### Task 6: Wiki Detail Page

**Files:**
- Rewrite: `portal/app/wiki/[slug]/page.tsx`
- Modify: `portal/components/artifact-viewer.tsx`

**Interfaces:**
- Consumes: `getDb()`, `assertInsideVault()`, `Artifact`, `parseTags()`, `.wiki-prose` from globals.css
- Produces: `/wiki/[slug]` detail page with two-column layout (content + metadata sidebar)

- [ ] **Step 1: Update artifact-viewer for dark theme**

Replace `portal/components/artifact-viewer.tsx`:

```tsx
"use client";

export function ArtifactViewer({ html }: { html: string }) {
  // Inject a style tag to force light background inside the iframe
  // (research artifacts are generated with white backgrounds)
  const styledHtml = `
    <style>
      html, body { background: #fff !important; color: #111 !important; }
    </style>
    ${html}
  `;

  return (
    <iframe
      srcDoc={styledHtml}
      sandbox="allow-scripts"
      className="w-full rounded-xl"
      style={{
        height: "80vh",
        minHeight: "600px",
        border: "1px solid rgba(255,255,255,0.06)",
      }}
      title="Artifact content"
    />
  );
}
```

- [ ] **Step 2: Write wiki detail page**

Replace `portal/app/wiki/[slug]/page.tsx`:

```tsx
import fs from "node:fs";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Calendar, Tag, Clock } from "lucide-react";
import { ArtifactViewer } from "@/components/artifact-viewer";
import { getDb } from "@/lib/db";
import { assertInsideVault } from "@/lib/path-guard";
import type { Artifact } from "@/lib/types";
import { parseTags } from "@/lib/utils";

function readHtmlContent(artifact: Artifact): string | null {
  if (!artifact.html_path) return null;
  try {
    const safePath = assertInsideVault(artifact.html_path);
    if (!fs.existsSync(safePath)) return null;
    return fs.readFileSync(safePath, "utf-8");
  } catch {
    return null;
  }
}

function estimateReadingTime(text: string): number {
  const words = text.split(/\s+/).length;
  return Math.max(1, Math.round(words / 200));
}

export default async function WikiDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;

  let artifact: Artifact | undefined;
  try {
    const db = getDb();
    artifact = db.prepare("SELECT * FROM artifacts WHERE slug = ?").get(slug) as
      | Artifact
      | undefined;
  } catch (err) {
    console.error("[WikiDetail] DB error for slug", slug, err);
    notFound();
  }

  if (!artifact) notFound();

  const tags = parseTags(artifact.tags);
  const date = artifact.created_at.slice(0, 10);
  const htmlContent = readHtmlContent(artifact);
  const readTime = estimateReadingTime(artifact.summary ?? "");

  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-6xl px-6 py-8">
        {/* Breadcrumb */}
        <nav className="mb-8">
          <Link
            href="/wiki"
            className="inline-flex items-center gap-1.5 text-sm transition-colors hover:text-[#f5f5f4]"
            style={{ color: "rgba(245,245,244,0.4)" }}
          >
            <ArrowLeft size={14} />
            Back to Wiki
          </Link>
        </nav>

        <div className="flex flex-col lg:flex-row gap-10">
          {/* Content */}
          <div className="flex-1 min-w-0">
            <header className="mb-8">
              <h1
                className="text-2xl sm:text-3xl font-semibold tracking-tight"
                style={{ color: "#f5f5f4", letterSpacing: "-0.02em" }}
              >
                {artifact.title}
              </h1>

              {artifact.summary && (
                <p
                  className="mt-4 font-serif italic text-lg leading-relaxed"
                  style={{ color: "rgba(245,245,244,0.6)" }}
                >
                  {artifact.summary}
                </p>
              )}
            </header>

            {htmlContent ? (
              <ArtifactViewer html={htmlContent} />
            ) : (
              <div className="surface-card p-8">
                <div className="wiki-prose">
                  <p>{artifact.summary}</p>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <aside className="w-full lg:w-[280px] flex-shrink-0">
            <div className="lg:sticky lg:top-[68px] space-y-6">
              {/* Metadata card */}
              <div className="surface-card p-5 space-y-4">
                <h4
                  className="text-[11px] font-medium uppercase tracking-wider"
                  style={{ color: "rgba(245,245,244,0.35)" }}
                >
                  Details
                </h4>

                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Calendar size={13} style={{ color: "rgba(245,245,244,0.3)" }} />
                    <span className="text-sm" style={{ color: "rgba(245,245,244,0.6)" }}>
                      {date}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock size={13} style={{ color: "rgba(245,245,244,0.3)" }} />
                    <span className="text-sm" style={{ color: "rgba(245,245,244,0.6)" }}>
                      {readTime} min read
                    </span>
                  </div>
                </div>

                {tags.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Tag size={13} style={{ color: "rgba(245,245,244,0.3)" }} />
                      <span
                        className="text-[11px] font-medium uppercase tracking-wider"
                        style={{ color: "rgba(245,245,244,0.35)" }}
                      >
                        Tags
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {tags.map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-0.5 rounded text-[11px] font-medium"
                          style={{
                            background: "rgba(255,255,255,0.04)",
                            color: "rgba(245,245,244,0.5)",
                            border: "1px solid rgba(255,255,255,0.06)",
                          }}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Verify build and visual check**

```bash
cd portal && bun run build && bun dev
```

Open `http://localhost:3000/wiki` → click an artifact → confirm two-column layout with content and sidebar metadata.

- [ ] **Step 4: Commit**

```bash
git add portal/app/wiki/[slug]/page.tsx portal/components/artifact-viewer.tsx
git commit -m "feat(portal): add wiki detail page with two-column layout"
```

---

### Task 7: Search / Ask AI Page

**Files:**
- Rewrite: `portal/app/search/page.tsx`

**Interfaces:**
- Consumes: `chat()` from `lib/chat.ts`, `/api/search` route, `.surface-card` / `.input-field` / `.btn-primary` from globals.css
- Produces: `/search` page with two tabs — "Ask AI" (RAG Q&A) and "Search" (keyword filtering)

- [ ] **Step 1: Write the search page**

Replace `portal/app/search/page.tsx`:

```tsx
"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { Search, Sparkles, Loader2, ArrowRight } from "lucide-react";
import { type ChatResponse, type ChatSource, chat } from "@/lib/chat";
import type { Artifact } from "@/lib/types";

type Tab = "ask" | "search";

export default function SearchPage() {
  const [activeTab, setActiveTab] = useState<Tab>("ask");

  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-3xl px-6 py-12">
        <header className="mb-8">
          <span className="kicker">Intelligence layer</span>
          <h1 className="section-title mt-2">Search your knowledge</h1>
        </header>

        {/* Tab switcher */}
        <div className="flex gap-1 mb-8 p-1 rounded-xl w-fit" style={{ background: "rgba(255,255,255,0.04)" }}>
          <TabButton active={activeTab === "ask"} onClick={() => setActiveTab("ask")}>
            <Sparkles size={13} />
            Ask AI
          </TabButton>
          <TabButton active={activeTab === "search"} onClick={() => setActiveTab("search")}>
            <Search size={13} />
            Search
          </TabButton>
        </div>

        {activeTab === "ask" ? <AskAITab /> : <SearchTab />}
      </div>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all"
      style={{
        background: active ? "rgba(255,255,255,0.08)" : "transparent",
        color: active ? "#f5f5f4" : "rgba(245,245,244,0.45)",
      }}
    >
      {children}
    </button>
  );
}

/* ── Ask AI Tab ─────────────────────────────────── */

function AskAITab() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await chat(trimmed);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get answer");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="flex gap-3">
        <div className="relative flex-1">
          <Sparkles
            size={16}
            className="absolute left-4 top-1/2 -translate-y-1/2"
            style={{ color: "#d4a574" }}
          />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask anything about your research…"
            disabled={loading}
            className="input-field pl-11"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="btn-primary disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : "Ask"}
        </button>
      </form>

      {error && (
        <div
          className="mt-6 p-4 rounded-xl text-sm"
          style={{
            background: "rgba(239,68,68,0.08)",
            border: "1px solid rgba(239,68,68,0.2)",
            color: "#fca5a5",
          }}
        >
          {error}
        </div>
      )}

      {loading && (
        <div className="mt-8 flex items-center gap-2" style={{ color: "rgba(245,245,244,0.45)" }}>
          <Loader2 size={14} className="animate-spin" />
          <span className="text-sm">Searching corpus and generating answer…</span>
        </div>
      )}

      {result && (
        <div className="mt-8 space-y-6 animate-fade-in">
          {/* Answer */}
          <div className="surface-card p-6">
            <h3
              className="text-[11px] font-medium uppercase tracking-wider mb-3"
              style={{ color: "rgba(245,245,244,0.35)" }}
            >
              Answer
            </h3>
            <div className="wiki-prose text-sm leading-relaxed">{result.answer}</div>
          </div>

          {/* Sources */}
          {result.sources.length > 0 && (
            <div>
              <h3
                className="text-[11px] font-medium uppercase tracking-wider mb-3"
                style={{ color: "rgba(245,245,244,0.35)" }}
              >
                Sources ({result.sources.length})
              </h3>
              <div className="space-y-2">
                {result.sources.map((source) => (
                  <SourceCard key={`${source.slug}-${source.excerpt.slice(0, 20)}`} source={source} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function SourceCard({ source }: { source: ChatSource }) {
  const matchColors: Record<string, string> = {
    vector: "#C7B8FF",
    fts: "#7BD0E8",
    hybrid: "#d4a574",
  };
  const color = matchColors[source.match_type] ?? "rgba(245,245,244,0.4)";

  return (
    <Link href={`/wiki/${source.slug}`}>
      <div className="surface-card p-4 flex items-start gap-4 group">
        <div className="flex-1 min-w-0">
          <h4
            className="text-sm font-medium truncate group-hover:text-[#f5f5f4] transition-colors"
            style={{ color: "rgba(245,245,244,0.8)" }}
          >
            {source.title}
          </h4>
          <p
            className="text-xs mt-1 line-clamp-2"
            style={{ color: "rgba(245,245,244,0.4)" }}
          >
            {source.excerpt}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span
            className="text-[10px] font-medium px-2 py-0.5 rounded-full uppercase"
            style={{ background: `${color}15`, color }}
          >
            {source.match_type}
          </span>
          <span
            className="text-[11px] font-mono tabular-nums"
            style={{ color: "rgba(245,245,244,0.3)" }}
          >
            {source.score.toFixed(2)}
          </span>
        </div>
      </div>
    </Link>
  );
}

/* ── Search Tab ─────────────────────────────────── */

function SearchTab() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Artifact[] | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    abortRef.current?.abort();

    const q = query.trim();
    if (!q) {
      setResults(null);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      const controller = new AbortController();
      abortRef.current = controller;
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`, {
          signal: controller.signal,
        });
        if (!res.ok) {
          setResults([]);
          return;
        }
        setResults((await res.json()) as Artifact[]);
      } catch (err) {
        if (err instanceof Error && err.name === "AbortError") return;
        setResults([]);
      }
    }, 300);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      abortRef.current?.abort();
    };
  }, [query]);

  return (
    <div>
      <div className="relative">
        <Search
          size={16}
          className="absolute left-4 top-1/2 -translate-y-1/2"
          style={{ color: "rgba(245,245,244,0.3)" }}
        />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by keyword…"
          className="input-field pl-11"
        />
      </div>

      {results !== null && (
        <div className="mt-6">
          {results.length === 0 ? (
            <p className="text-sm text-center py-12" style={{ color: "rgba(245,245,244,0.4)" }}>
              No results for &ldquo;{query.trim()}&rdquo;
            </p>
          ) : (
            <div className="space-y-2">
              {results.map((artifact) => (
                <Link key={artifact.id} href={`/wiki/${artifact.slug}`}>
                  <div className="surface-card p-4 group">
                    <h4
                      className="text-sm font-medium group-hover:text-[#f5f5f4] transition-colors"
                      style={{ color: "rgba(245,245,244,0.8)" }}
                    >
                      {artifact.title}
                    </h4>
                    <p
                      className="text-xs mt-1 line-clamp-1"
                      style={{ color: "rgba(245,245,244,0.4)" }}
                    >
                      {artifact.summary}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      )}

      {results === null && (
        <p className="text-sm text-center py-12" style={{ color: "rgba(245,245,244,0.3)" }}>
          Start typing to search across all artifacts.
        </p>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verify build and visual check**

```bash
cd portal && bun run build && bun dev
```

Open `http://localhost:3000/search` — confirm tab switcher works, Ask AI form submits (needs Python server running), Search tab filters instantly.

- [ ] **Step 3: Commit**

```bash
git add portal/app/search/page.tsx
git commit -m "feat(portal): add search page with Ask AI and keyword search tabs"
```

---

### Task 8: README & Branding Updates

**Files:**
- Rewrite: `README.md` (project root)
- Modify: `VISION.md`, `ROADMAP.md`, `CAPABILITIES.md`, `CHANGELOG.md` — find/replace "Evo" → "EvoMind" in titles and visible copy (leave code paths and internal references as-is)

**Interfaces:**
- Produces: Portfolio-ready README and consistent branding across docs

- [ ] **Step 1: Write new README.md**

Replace the project root `README.md`:

```markdown
# EvoMind

> AI-powered personal knowledge base with hybrid RAG retrieval, autonomous research agents, and a compounding knowledge graph.

**"The goal isn't to remember everything. It's to never lose what matters."**

## What This Demonstrates

| Capability | Implementation |
|---|---|
| **Hybrid RAG Retrieval** | Vector search (sqlite-vec, Cohere Embed v4 at 1024 dims) + FTS5 full-text search, fused via score-based merge |
| **Research Agents** | Autonomous tool-calling loop: retrieve → generate → ingest. Allowlist-enforced, fully audited. |
| **Embedding Pipeline** | Sentence-boundary chunking, batched embedding with exponential backoff, incremental + full rebuild |
| **Eval Harness** | 10-question retrieval quality gate — currently 10/10. No change ships if retrieval regresses. |
| **Provider Abstraction** | BedrockProvider (Claude Sonnet 4.6 + Cohere Embed v4). Swappable via `EVO_LLM_PROVIDER`. |
| **Migration-Versioned Schema** | Forward-only SQL migrations. SQLite + sqlite-vec + FTS5 in a single local file. |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Portal (Next.js 16, React 19, Tailwind v4)         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Landing   │  │ Wiki     │  │ Search   │          │
│  │ Page      │  │ Browser  │  │ Ask AI   │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
│       │              │              │                │
│  SQLite (readonly)   │         POST /chat            │
│  better-sqlite3      │              │                │
└──────────────────────┼──────────────┼────────────────┘
                       │              │
┌──────────────────────┼──────────────┼────────────────┐
│  Server (FastAPI)    │              │                │
│  ┌───────────────────▼──────────────▼───────────┐    │
│  │  Hybrid Retrieval: vec_search + fts_search   │    │
│  │  → score-based merge → dedup by chunk_id     │    │
│  └──────────────────────────────────────────────┘    │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────┐   │
│  │ Research    │  │ Provider     │  │ Embedding │    │
│  │ Agent       │  │ (Bedrock)    │  │ Pipeline  │    │
│  └─────────────┘  └──────────────┘  └───────────┘   │
│  ┌─────────────┐  ┌──────────────┐                   │
│  │ Tool Router │  │ Governance   │                   │
│  │ + Allowlist │  │ + Audit Log  │                   │
│  └─────────────┘  └──────────────┘                   │
└──────────────────────────────────────────────────────┘
                       │
              ┌────────▼────────┐
              │  manifest.db    │
              │  SQLite + FTS5  │
              │  + sqlite-vec   │
              └─────────────────┘
```

## Tech Stack

**Backend:** Python 3.12+ · FastAPI · SQLite (FTS5 + sqlite-vec) · AWS Bedrock (Claude Sonnet 4.6 + Cohere Embed v4) · pytest (153 tests)

**Frontend:** Next.js 16 · React 19 · Tailwind v4 · shadcn/ui · better-sqlite3

## Run Locally

### Prerequisites
- Python 3.12+, [uv](https://docs.astral.sh/uv/)
- Node.js 20+, [bun](https://bun.sh)
- AWS credentials with Bedrock access (`AWS_PROFILE` + `AWS_REGION` in env)

### Backend
```bash
# Apply migrations
uv run scripts/migrate.py

# Embed existing artifacts (if any)
uv run scripts/embed.py --incremental

# Start server
uvicorn server:app --port 8765
```

### Portal
```bash
cd portal
bun install
bun dev
```

Open `http://localhost:3000`

### Ingest research
```bash
uv run scripts/ingest.py --title "..." --slug "..." --tags "..." --topics "..." --summary "..." --html /path/to/file.html
```

### Run tests
```bash
uv run pytest                    # 153 Python tests
cd portal && bun test            # Portal tests
cd portal && bun run build       # Build check
uv run scripts/eval.py           # Retrieval quality gate (10/10)
```

## License

MIT
```

- [ ] **Step 2: Update branding in project docs**

In `VISION.md`, `ROADMAP.md`, `CAPABILITIES.md`, `CHANGELOG.md` — replace the first-line title and any prominent "Evo" references with "EvoMind". Leave internal code paths (`EVO_STORE`, `EVO_SERVER_URL`, etc.) unchanged since those are actual env var names.

Use find/replace judiciously — only visible titles and descriptions, not code references.

- [ ] **Step 3: Commit**

```bash
git add README.md VISION.md ROADMAP.md CAPABILITIES.md CHANGELOG.md
git commit -m "docs: rebrand to EvoMind, rewrite README for portfolio"
```

---

### Task 9: Final Verification

**Files:** None new — verification only.

- [ ] **Step 1: Run Python tests**

```bash
uv run pytest
```

Expected: 153 passing, 2 skipped. Zero failures. Backend untouched.

- [ ] **Step 2: Run portal tests**

```bash
cd portal && bun test
```

Expected: Search and artifact API route tests pass. Agent/teach tests were deleted. Note any failures from import path changes (e.g., tests importing `artifact-card` that no longer exists) and fix them.

- [ ] **Step 3: Build portal**

```bash
cd portal && bun run build
```

Expected: Clean build, no errors.

- [ ] **Step 4: Visual walkthrough**

Start both servers:
```bash
# Terminal 1
uvicorn server:app --port 8765

# Terminal 2
cd portal && bun dev
```

Walk through all 4 pages:
1. `http://localhost:3000` — Landing with hero, feature cards, tech stack, tagline
2. `http://localhost:3000/wiki` — Grid of artifacts, search works, tag filters work
3. Click an artifact → `/wiki/[slug]` — Two-column layout, content renders, sidebar shows metadata
4. `http://localhost:3000/search` — Tab switcher, Ask AI returns cited answer, Search filters instantly

Confirm:
- No white flashes or unstyled elements
- Dark theme consistent across all pages
- Navigation works between all pages
- Mobile responsive (resize browser)

- [ ] **Step 5: Fix any issues found, commit**

```bash
git add -A
git commit -m "fix(portal): address final verification issues"
```

- [ ] **Step 6: Tag release**

```bash
git tag -a v0.4.0-evomind -m "EvoMind portfolio reskin"
```
