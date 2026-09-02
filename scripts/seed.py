"""Seed manifest.db with demo research artifacts for portfolio presentation."""

import sqlite3
import sys
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "manifest.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    tags TEXT NOT NULL DEFAULT '',
    topics TEXT NOT NULL DEFAULT '',
    html_path TEXT,
    md_path TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE VIRTUAL TABLE IF NOT EXISTS artifacts_fts USING fts5(
    title, summary, tags, topics,
    content='artifacts',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS artifacts_ai AFTER INSERT ON artifacts BEGIN
    INSERT INTO artifacts_fts(rowid, title, summary, tags, topics)
    VALUES (new.id, new.title, new.summary, new.tags, new.topics);
END;

CREATE TRIGGER IF NOT EXISTS artifacts_ad AFTER DELETE ON artifacts BEGIN
    INSERT INTO artifacts_fts(artifacts_fts, rowid, title, summary, tags, topics)
    VALUES ('delete', old.id, old.title, old.summary, old.tags, old.topics);
END;

CREATE TRIGGER IF NOT EXISTS artifacts_au AFTER UPDATE ON artifacts BEGIN
    INSERT INTO artifacts_fts(artifacts_fts, rowid, title, summary, tags, topics)
    VALUES ('delete', old.id, old.title, old.summary, old.tags, old.topics);
    INSERT INTO artifacts_fts(rowid, title, summary, tags, topics)
    VALUES (new.id, new.title, new.summary, new.tags, new.topics);
END;
"""

ARTIFACTS = [
    {
        "slug": "retrieval-augmented-generation",
        "title": "Retrieval-Augmented Generation (RAG)",
        "summary": "RAG combines retrieval systems with generative models to produce grounded, factual responses. Instead of relying solely on parametric knowledge, the model retrieves relevant documents at inference time and conditions its generation on them. This reduces hallucination and allows the system to access knowledge beyond its training cutoff. Key design decisions include chunk size, embedding model selection, retrieval strategy (dense vs sparse vs hybrid), and how retrieved context is injected into the prompt.",
        "tags": "rag,retrieval,llm,architecture",
        "topics": "retrieval-augmented-generation,vector-search,grounding",
        "created_at": "2026-04-12 09:30:00",
    },
    {
        "slug": "hybrid-search-strategies",
        "title": "Hybrid Search: Vector + Full-Text Fusion",
        "summary": "Neither vector search nor keyword search alone covers the full question space. Vector search excels at semantic similarity but misses exact terms. Full-text search (BM25/FTS5) excels at exact matching but misses paraphrases. Hybrid search fuses both: run vector and keyword searches in parallel, normalize scores, and merge results with deduplication. The merge strategy matters — reciprocal rank fusion (RRF) and score-based weighted merge are the two dominant approaches. EvoMind uses score-based merge with dedup by chunk_id.",
        "tags": "retrieval,search,vector-search,fts5,hybrid",
        "topics": "hybrid-search,bm25,vector-similarity,score-fusion",
        "created_at": "2026-04-18 14:15:00",
    },
    {
        "slug": "embedding-models-comparison",
        "title": "Embedding Models: Cohere, OpenAI, and Open-Source Alternatives",
        "summary": "Embedding model choice directly impacts retrieval quality. Cohere Embed v4 offers strong multilingual performance at 1024 dimensions with efficient batching. OpenAI's text-embedding-3-large provides 3072 dimensions but at higher cost. Open-source alternatives like BGE, E5, and GTE match proprietary models on MTEB benchmarks while running locally. Key tradeoffs: dimension count affects storage and search speed, API-based models add latency and cost, and domain-specific fine-tuning can dramatically improve recall for specialized corpora.",
        "tags": "embeddings,cohere,openai,retrieval,comparison",
        "topics": "embedding-models,vector-dimensions,mteb-benchmark",
        "created_at": "2026-04-25 11:00:00",
    },
    {
        "slug": "agent-tool-calling-patterns",
        "title": "Agent Tool-Calling Patterns and Execution Loops",
        "summary": "LLM agents extend beyond single-turn generation by calling tools in a loop. The agent receives a task, reasons about which tool to call, executes it, observes the result, and decides whether to call another tool or produce a final answer. Key patterns: ReAct (reason-then-act), function calling with structured outputs, and multi-step planning. Tool allowlists constrain what an agent can do — a safety and composability property. Every tool call should be logged for auditability and replay. The execution loop is the core primitive; everything else plugs into it.",
        "tags": "agents,tools,llm,architecture,patterns",
        "topics": "tool-calling,react-pattern,agent-loop,allowlist",
        "created_at": "2026-05-03 10:45:00",
    },
    {
        "slug": "sqlite-as-vector-database",
        "title": "SQLite as a Vector Database: sqlite-vec and FTS5",
        "summary": "For single-user local-first applications, SQLite with sqlite-vec provides vector search without the operational overhead of Pinecone, Weaviate, or Qdrant. sqlite-vec stores embeddings in a virtual table using vec0, supports cosine similarity search, and integrates naturally with existing SQLite queries. Combined with FTS5 for full-text search, a single manifest.db file becomes a hybrid retrieval engine. Tradeoffs: no distributed scaling, no built-in HNSW (brute-force kNN), and embedding dimensions are fixed at table creation. For corpora under 100K chunks, performance is excellent.",
        "tags": "sqlite,vector-search,sqlite-vec,fts5,local-first",
        "topics": "sqlite-vec,vector-database,local-first,hybrid-retrieval",
        "created_at": "2026-05-10 16:20:00",
    },
    {
        "slug": "prompt-engineering-for-research-agents",
        "title": "Prompt Engineering for Autonomous Research Agents",
        "summary": "Research agents need carefully structured system prompts that define their role, available tools, output format, and constraints. The prompt must specify: what the agent is (a research assistant), what tools it can call (retrieve, generate, ingest), what output format to produce (structured notes with sections), and what it must not do (fabricate sources, exceed scope). Few-shot examples of tool call sequences improve reliability. Chain-of-thought reasoning in the system prompt helps the agent plan multi-step research workflows. The prompt is the agent's skill definition.",
        "tags": "prompts,agents,research,engineering",
        "topics": "system-prompts,agent-instructions,chain-of-thought",
        "created_at": "2026-05-15 08:30:00",
    },
    {
        "slug": "eval-driven-development",
        "title": "Eval-Driven Development for RAG Systems",
        "summary": "Without evals, RAG quality is unmeasurable. An eval harness defines a set of questions with known-good retrieval targets, runs them against the system, and gates releases on a quality threshold. EvoMind's harness uses 10 questions spanning different query types (factual, conceptual, comparative) and requires at least 8/10 to pass. Currently scoring 10/10. The eval runs retrieval only — no generation cost. This separates retrieval quality from generation quality, making regressions attributable. Every schema change, every embedding model swap, every chunking adjustment runs through the eval before merging.",
        "tags": "evals,testing,rag,quality,retrieval",
        "topics": "eval-harness,retrieval-quality,regression-testing",
        "created_at": "2026-05-22 13:00:00",
    },
    {
        "slug": "chunking-strategies-for-retrieval",
        "title": "Text Chunking Strategies for Retrieval Quality",
        "summary": "How you split documents into chunks directly affects retrieval precision and recall. Fixed-size chunking (e.g., 800 tokens with 100-token overlap) is simple and predictable. Sentence-boundary chunking respects natural language boundaries, producing more coherent chunks. Semantic chunking groups related sentences by embedding similarity. Heading-aware chunking uses document structure to create topically coherent chunks. EvoMind uses sentence-boundary chunking at 800 characters with 100-character overlap — a pragmatic choice that balances coherence with simplicity. The eval harness validates that the chosen strategy actually works.",
        "tags": "chunking,retrieval,text-processing,nlp",
        "topics": "text-chunking,sentence-boundary,overlap-strategy",
        "created_at": "2026-05-28 09:15:00",
    },
    {
        "slug": "provider-abstraction-for-llm-applications",
        "title": "Provider Abstraction: Avoiding LLM Vendor Lock-In",
        "summary": "A provider abstraction defines a protocol (interface) that any LLM vendor must implement: chat completion, embedding generation, and model metadata. The application code calls the protocol, never the vendor SDK directly. This makes switching from OpenAI to Bedrock to a local model a configuration change, not a rewrite. EvoMind's BedrockProvider implements the Provider protocol using boto3, routing chat to Claude Sonnet 4.6 and embeddings to Cohere Embed v4. The provider is selected at startup via the EVO_LLM_PROVIDER environment variable. Cost tracking is per-provider — each provider reports token counts in its response.",
        "tags": "llm,architecture,abstraction,bedrock,provider",
        "topics": "provider-pattern,vendor-abstraction,bedrock,boto3",
        "created_at": "2026-06-01 15:45:00",
    },
    {
        "slug": "governance-and-audit-for-ai-agents",
        "title": "Governance and Audit Logging for AI Agent Systems",
        "summary": "Non-deterministic agent behavior requires audit infrastructure from day one. Every agent run should record: the task input, every tool call made (name, input, output, duration), the final output, total token cost, and whether the run succeeded or failed. This enables replay, debugging, cost attribution, and compliance. Tool allowlists enforce that agents can only call approved tools — a safety boundary that prevents scope creep. Failed runs must record the error and all tool calls made before the failure, not just the error message. The audit log is the foundation for trust in autonomous systems.",
        "tags": "governance,audit,agents,safety,logging",
        "topics": "audit-log,tool-allowlist,agent-governance,cost-tracking",
        "created_at": "2026-06-08 11:30:00",
    },
]


def seed():
    DB_DIR.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        print(f"DB already exists at {DB_PATH}")
        print("Delete it first if you want to re-seed: rm data/manifest.db")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript(SCHEMA)

    for art in ARTIFACTS:
        conn.execute(
            """
            INSERT INTO artifacts (slug, title, summary, tags, topics, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                art["slug"],
                art["title"],
                art["summary"],
                art["tags"],
                art["topics"],
                art["created_at"],
                art["created_at"],
            ),
        )

    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]
    conn.close()

    print(f"Seeded {count} artifacts into {DB_PATH}")


if __name__ == "__main__":
    seed()
