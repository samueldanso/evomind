# Evo — Product Vision

> Spin up agents to go deep on anything. They research, write notes, teach you. It compounds.

## One-liner

EvoResearch is an agent-first learning platform. You direct agents to go deep on a topic. They research it, write structured notes into your knowledge base, then teach you from those notes. Every session compounds into the next. Chat is how you retrieve what the agents built.

---

## The north star

**Agents do the work. You direct them. The KB is what they build. Chat is how you query what they built.**

This is not a chatbot you ask questions to. This is a platform you direct agents through. The distinction is architectural, not cosmetic. It determines what gets built first, what the primary interface is, and what the product is actually defending.

---

## The core loop

```
You: "go deep on KV Cache"
        ↓
Research Agent spins up
  → web_search: finds primary sources, papers, engineering blogs
  → retrieve: pulls existing KB context on related concepts
  → generate: synthesizes findings into structured notes
  → ingest: writes notes as a structured artifact into KB
        ↓
Teaching Agent spins up (from the notes just written)
  → retrieve: pulls the notes the research agent just wrote
  → generate: teaches you layer by layer
  → quizzes you, verifies mastery before advancing
  → maps connections to concepts you already know
  → ingest: writes mastery checklist back into KB
        ↓
KB grows
  → notes on KV Cache now in KB
  → your mastery state recorded
  → connections to PagedAttention, batching, context windows mapped
        ↓
Next session on PagedAttention:
  → Research Agent pulls existing KV Cache notes as context
  → Teaching Agent knows you already understand KV Cache
  → Both sessions are richer because of what came before
        ↓
Later — you chat to retrieve
  → "explain KV Cache again"
  → "how does it connect to PagedAttention?"
  → "what did I struggle with last time?"
  → retrieval pulls from accumulated notes + mastery state
  → grounded answers with citations back to the notes agents wrote
```

The loop is the product. Every component exists to serve it.

---

## What each part is

**Agents** — the workers. They receive a task, call tools to do the work, write their output back to the KB. You direct them. They execute.

**Tools** — what agents call to do work. `web_search` finds sources. `retrieve` pulls KB context. `generate` synthesizes and teaches. `ingest` writes output back. Tools are bounded per agent — each agent has an explicit allowlist of what it can call.

**The KB** — what agents build over time. Not a file store. Structured notes, mastery checklists, concept connections, claim-level knowledge. It gets richer with every session.

**Chat** — how you query what agents built. Not the primary interface. The retrieval surface. You chat against a KB that agents already populated. Without the agents running first, chat has nothing meaningful to draw from.

**The skills** — the instruction sets agents follow. `research-wiki` tells the Research Agent how to structure its notes. `teach-me` tells the Teaching Agent how to teach incrementally and verify mastery. The agent is the runtime. The skill is the behavior.

---

## Engineering positioning

Evo is built as an **agent platform product, not a RAG app.**

The distinction:

| RAG app | Agent platform |
|---|---|
| User sends a query | User directs an agent |
| System retrieves and generates | Agent calls tools in a loop |
| Response returned | Output ingested back to KB |
| Nothing persists beyond the chat | KB compounds with every run |
| Chat is the product | Chat is the retrieval surface |
| Retrieval is the architecture | Retrieval is a tool agents call |

A RAG app calls a retriever and an LLM in sequence. An agent platform dispatches a task to an agent, the agent calls tools in a loop, the output is persisted to memory, and the next task starts richer than the last. The compounding is a structural property of the runtime — not a feature added later.

**The portfolio thesis:** this is what AI Platform Engineering looks like when it ships as a product people actually use. Not an app with a fancy stack. Not infrastructure with no surface. A real agent platform whose primary interface is agent invocation, whose primary output is a compounding knowledge base, and whose secondary interface is retrieval over what the agents built.

---

## The platform layers

```
┌─────────────────────────────────────────────────────────┐
│                     Control Surface                      │
│        Agent Invocation UI · Chat Retrieval · CLI        │
│        Agent invocation is primary. Chat is secondary.   │
├─────────────────────────────────────────────────────────┤
│                  Orchestration Layer                     │
│     Agent dispatcher · Task contracts · Tool router      │
│     Cost guardrails · Replay log · Async runtime         │
├─────────────────────────────────────────────────────────┤
│                     Agent Layer                          │
│   Research Agent · Teaching Agent · Fact-checker         │
│   Deepener · Reconciler                                  │
│   Each agent: scoped task + bounded tool allowlist       │
├─────────────────────────────────────────────────────────┤
│                     Tool Layer                           │
│   web_search() · retrieve() · generate() · ingest()      │
│   Each tool: typed input/output contract                 │
├─────────────────────────────────────────────────────────┤
│                    Memory Layer                          │
│   Structured notes · Mastery checklists                  │
│   Concept connections · Claim-level knowledge            │
│   Agent run log · Source provenance                      │
├─────────────────────────────────────────────────────────┤
│                    Storage Layer                         │
│   SQLite (FTS5 + sqlite-vec) · Migration versioned       │
│   Path-confined FS · Atomic upsert · Cascade clean       │
└─────────────────────────────────────────────────────────┘
```

The intelligence substrate (retrieval, embeddings, provider abstraction, eval harness) shipped in v0.2.0. The agent runtime lands in v0.3.0 — the first phase with executable agent behavior. Chat shipped in v0.2.0 and is reframed in v0.3.0 as the retrieval surface over what agents built. This ordering reflects the center of gravity: the agent runtime is the core. Retrieval, chat, and storage are the substrate it stands on.

---

## Architecture reference: Agent = LLM + Harness

Evo's architecture follows the industry-emerging *Agent = LLM + Harness* framework (NVIDIA GTC 2026). An agent is the LLM plus everything around it that makes the LLM useful in a loop: context assembly, the observe-reason-act cycle, memory that persists across runs, tools the agent can call, skills the agent follows, an orchestration layer that dispatches and chains agents, and security/governance that bounds behavior and audits it.

Evo's component map:

| Harness component | Evo implementation |
|---|---|
| **LLM** | Bedrock — Claude Sonnet 4.6 + Cohere Embed v4 via `core/llm/bedrock.py` |
| **Context** | Skill prompt + retrieved chunks + task input + tool results, assembled per turn |
| **Observe → Reason → Act** | Agent execution loop in `core/runtime/` (Phase D) |
| **Memory** | KB: `artifacts`, `chunks`, `embeddings`, `claims` (stub), mastery checklists, `agent_runs` log |
| **Tools & Skills** | `core/tools/` (retrieve, generate, ingest) + `core/prompts/` (research-wiki, teach-me skills) |
| **Prompt** | System prompts per skill + per-task input contracts (`ResearchTask`, `TeachTask`) |
| **Orchestration** | Agent dispatcher + Research → Teaching auto-chain (`core/runtime/`) |
| **Security & Governance** | Tool allowlist per agent + `agent_runs` audit log + cost tracking |

The "Platform layers" diagram above is Evo's specific instantiation of this framework. The harness components are the universal pattern; the layers diagram is the concrete code organization.

---

## The agents

**Research Agent** — researches a topic deeply. Calls `web_search`, `retrieve`, `generate`, `ingest`. Follows `research-wiki` skill. Ships in v0.3.0 (Phase D).

**Teaching Agent** — teaches you from what the Research Agent wrote. Calls `retrieve`, `generate`, `ingest`. Follows `teach-me` skill. Ships in v0.3.0 (Phase D).

**Fact-Checker** — verifies a claim against primary sources. Ships in v0.6.0 (Phase G).

**Deepener** — finds adjacent concepts and spawns Research + Teaching runs autonomously. Ships in v0.6.0 (Phase G).

**Reconciler** — resolves contradictions between notes by gathering more evidence. Ships in v0.6.0 (Phase G).

---

## The skills

Skills are instruction sets agents follow — not the agents themselves.

`research-wiki` — tells the Research Agent how to structure its notes. What sections to produce. How to write for future retrieval, not just for reading.

`teach-me` — tells the Teaching Agent how to teach. Layer by layer. Problem before solution. Quiz before advancing. Connections step at the end of every session.

Skills live as markdown files embedded in the agent's system prompt at runtime. Updating a skill updates every future run of that agent without touching the runtime.

---

## How memory compounds

Every agent run writes back to the KB:

- Notes accumulate on every topic you've directed agents to research
- Mastery state is recorded — what you know, what you struggled with, what you've connected
- Concept connections build — KV Cache links to PagedAttention links to batching
- The Research Agent uses existing notes as context when researching adjacent topics
- The Teaching Agent uses mastery state to skip what you know and focus on what you don't
- Chat retrieval draws from everything agents built — richer KB means richer answers

This compounding is not a feature. It is the structural consequence of every agent writing back to the same memory layer.

---

## What the job is

When you go deep on something the job is building durable understanding. Not collecting sources. Not reading articles. Building understanding that compounds and is there when you need it.

What people use today is a patchwork: browser tabs, ChatGPT for explanation, Notion for notes, their own memory to hold it together. The memory layer is the failure point. Understanding never accumulates. It evaporates.

Evo is the missing memory layer. Agents build it. You direct them. It compounds.

---

## What we are not building

- A chatbot — chat is a retrieval surface, not the product
- A RAG app with agents planned for later — agents are first, retrieval is a tool they use
- A note-taking app — notes are agent output, not user input
- A standalone fact-checker — fact-checking is an agent capability
- Real-time multi-user collaboration — single-user first
- Mobile native apps
- Hosted enterprise SaaS at launch — open-source v1 first
- A generic agent marketplace — agents here are research and learning specific

**Note on the v0.2.0 → v0.3.0 framing shift:** v0.2.0 shipped with chat as the visible surface and retrieval as the architectural foundation. v0.3.0 reframes the same code as substrate for the agent layer — retrieval becomes a tool agents call, chat becomes the surface for querying what agents built. No code is thrown away. The compounding agent-first product was always the destination; v0.2.0 built the substrate, v0.3.0 makes the agents the primary interface. Anyone reading the CHANGELOG sees the trail: substrate first, agents second, retrieval and chat repositioned as agent capabilities not the product itself.

---

## Positioning

If Hermes is "Cursor for everything you do", Evo is "Cursor for everything you learn."

Hermes acts on your tasks. Evo builds your understanding.

---

## Target users

1. **Builders going deep on new domains** — AI infra, web3, distributed systems. *This is Samuel.*
2. **CS / STEM students** — reconciling lectures, textbooks, blogs, AI explanations.
3. **Independent researchers** — tracking evolving fields where last month's source may be wrong.
4. **(Later) Small teams** — research groups, study groups.

---

## Why we win

| Competitor | What they do | Why we win |
|---|---|---|
| NotebookLM | RAG over uploaded files | You upload, it retrieves. No agents, no compounding, no teaching. |
| Perplexity | Web search + cited answer | Per-query. Nothing accumulates. No teaching. |
| ChatGPT with files | Upload and ask | Ephemeral. No memory across sessions. No agent loop. |
| Obsidian + plugins | RAG over your notes | You write the notes. No research agent. No teaching. |
| Onyx | Enterprise AI search | Enterprise-shaped. Not the individual learner. |
| R2R / LangGraph | RAG/agent frameworks | Infrastructure. Not a product. |

What nobody does: **spin up agents that research, write notes, and teach you — with a KB that compounds across every session.**

---

## Strategy

1. Build for Samuel first. Use daily. If it doesn't become a daily driver, the public version isn't worth shipping.
2. Ship to GitHub as v1.0 only when it works for the original user every day.
3. Hosted version is optional and last. Only if open source demonstrates demand.

---

## Decision principle

When a feature decision is unclear:

> Does this make the agent loop richer, or does it just add features?

Richer agent loop wins. Features don't.
