# EvoResearch — Product Vision

> Your learning partner. Builds and protects your understanding of any domain you choose to go deep on.

## One-liner

EvoResearch is a learning and research partner that turns scattered sources into compounding personal expertise. It ingests notes, lectures, articles, research, and codebases; structures them into understanding; keeps that understanding honest as you grow it; and serves it back through chat, browse, and agent loops.

## The job

When you go deep on something — a domain you're learning (AI infra, web3, distributed systems), a topic you're studying (algebra, organic chem, macroecon), a codebase you're inheriting, a field you're tracking — the actual job is **building durable understanding**.

That job has stages:

- Pulling sources from many places: notes, lectures, papers, blogs, AI-generated research
- Making sense of them together — which is hard because sources overlap, contradict, and age differently
- Holding what you learn so it compounds rather than evaporating
- Using that understanding later to answer questions, make decisions, write things, build things

What people use today is a patchwork: Notion or Obsidian for storage, ChatGPT for explanation, Perplexity for fact-checking, browser tabs for sources, and their own memory to hold it together. The memory layer is the failure point. Everything else is fine alone, but the *understanding* never accumulates anywhere — it stays in your head and decays.

## What we are

EvoResearch is the missing memory layer. Not a notes app. Not a chatbot. Not a search engine. **A learning partner that builds and holds your understanding of a domain, and grows it as you grow.**

Reconciliation, contradiction detection, fact-checking — these are how the system keeps your understanding honest as it grows. They are quality mechanisms in service of the value, not the value itself.

The value is depth of understanding over time. The mechanisms are what protect that depth.

## The loop

```
sources → understanding → kept honest → served back
   ▲                                          │
   └──────────────────────────────────────────┘
              you keep adding, it keeps growing
```

- **Sources** — any input you feed it: HTML pages, lecture PDFs, blog URLs, Markdown notes, codebases (later)
- **Understanding** — structured knowledge, not stored documents. The system extracts what's being said, links it across sources, and builds a representation of what you collectively know about the topic
- **Kept honest** — when sources contradict, the system flags it. When new sources update old ones, the older content is superseded. Fact-check agents (Phase F) can verify against primary sources. These are quality mechanisms, not the product
- **Served back** — through chat with citations, through browse and search, and through spawned research agents that extend what you know

The defensible thing isn't any single step. It's that the system gets smarter about your domains the longer you use it, because every source you feed it compounds into something larger than the sum of the sources.

## Positioning

Hermes is the general productivity and coding agent. EvoResearch is its research and learning counterpart. Same builder, same ergonomic bar, different domain.

If Hermes is "Cursor for everything you do", EvoResearch is "Cursor for everything you learn".

## Target users (priority order)

1. **Builders learning new domains** — AI infra, web3, distributed systems, ML research. They consume content aggressively and need it to compound. *This is Samuel.*
2. **CS / STEM students** — reconciling lecture notes, textbooks, blog articles, and ChatGPT explanations. Contradictions are the norm.
3. **Independent researchers tracking evolving fields** — where last month's blog post may now be wrong.
4. **(Later) Small teams sharing understanding** — research groups, study groups, founder + technical advisor pairs.

Explicitly **not** the target: enterprises, sales teams, customer support knowledge bases. That's Onyx territory.

## Why we win

| Competitor | What they do | Why we win |
|---|---|---|
| NotebookLM | Cloud RAG over user files | Closed; no evolution; understanding doesn't compound across sessions |
| Onyx | Enterprise AI search over 50+ sources | Enterprise-shaped, not the individual learner |
| OpenAgent | General-purpose self-hosted agent | No research specialisation; no claim-level reasoning |
| R2R / Haystack / LangGraph | RAG frameworks | Infrastructure, not a product |
| Obsidian plugins (Smart Connections, Copilot) | RAG over vault | Notes-only; no external ingest; no reconciliation |
| Perplexity | Live web search + cited answer | Per-query; doesn't compound your understanding |
| ChatGPT with files | Upload-and-ask | Ephemeral; no memory of past sessions or sources |

The defensible combination: **multi-source ingest + structured understanding that compounds + quality mechanisms that keep it honest + clean local-first product with a path to open source.**

No one is selling depth-of-understanding-over-time as a product. They're selling search, chat, or storage. We're selling the layer that turns those into expertise.

## What we are not building

To prevent scope creep, the following are explicitly out of scope:

- A general-purpose AI chat assistant (we are not building a Claude / ChatGPT clone)
- A standalone fact-checker (fact-checking serves learning here; it is not the product)
- Real-time multi-user collaboration (single-user first; teams much later)
- Mobile native apps
- Hosted enterprise SaaS at launch (open-source v1 ships first; hosted is optional Phase I)
- Voice / audio ingest (text and HTML / PDF / MD first)
- A generic agent marketplace (agents in EvoResearch are research-specific)

## Product-market-fit signals

**Personal (Samuel as user one)**

- Samuel uses EvoResearch daily for at least 30 days without skipping
- Samuel can answer questions about a domain he's been ingesting that he could not have answered without the system
- EvoResearch surfaces at least one correction or update per week that Samuel didn't catch himself

**Public (post open source)**

- 1,000+ GitHub stars within 6 months of v1.0 release
- 50+ active self-hosters who installed and ingested more than 10 sources
- Organic install requests in builder communities (X, Discord, HN, builder Slack channels)
- 5+ community-contributed ingest plugins

**Retention** (the strongest signal that the value is real)

- Users return to query their KB weeks after building it — memory is the value
- Users add new sources over time — the understanding grows, not stagnates
- At least one user reports publicly that EvoResearch helped them go deeper on something they were learning

## Strategy: personal-first, then open source, then optional hosted

1. **Build for Samuel first.** Use it daily. If it does not become a daily-driver tool, the public version is not worth shipping.
2. **Ship to GitHub as v1.0 only when it works for the original user every day.** No vanity OSS release.
3. **Open-source release is a quality bar, not a milestone.** Match what Hermes, Cursor, Codex deliver in production quality.
4. **Hosted version is optional and last.** Only if open source demonstrates demand.

This mirrors how the job-ops system reference example shipped (built for self, used to land a FAANG offer, then open-sourced to 20k+ stars). Personal use validates the product before the world sees it.

## Decision principle for trade-offs

When a feature decision is unclear, the tie-breaker is:

> Does this deepen the user's understanding of their domain over time, or does it just add features?

Deepening understanding wins. Features don't.

- A nicer search UI does not deepen understanding. Contradiction detection does.
- A new file format does not deepen understanding. Compounding across sources does.
- A team-sharing feature does not deepen understanding. Letting agents extend your learning does.
- A pretty chat UI does not deepen understanding. Cited retrieval that lets you trust the answer does.

This is the lens for every roadmap call.
