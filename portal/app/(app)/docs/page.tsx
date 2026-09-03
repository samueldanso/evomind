import Link from "next/link";

const STEPS = [
  {
    number: "01",
    title: "Add a source",
    description:
      "Paste text or research notes. EvoMind chunks and embeds it automatically using sentence-boundary splitting and vector embeddings.",
    href: "/ingest",
    linkLabel: "Add a source",
  },
  {
    number: "02",
    title: "Browse the wiki",
    description:
      "All your research appears as cards you can filter by tags and search. Each article stores the original text alongside chunked, embedded representations.",
    href: "/wiki",
    linkLabel: "Open wiki",
  },
  {
    number: "03",
    title: "Ask questions",
    description:
      "Use the Ask AI feature to get cited answers grounded in your knowledge base. Hybrid retrieval combines vector similarity with full-text search for accurate results.",
    href: "/wiki",
    linkLabel: "Try it",
  },
  {
    number: "04",
    title: "Search",
    description:
      "Keyword search powered by SQLite FTS5 for instant results across your entire knowledge base. Search titles, tags, topics, and full article content.",
    href: "/search",
    linkLabel: "Search now",
  },
];

export default function DocsPage() {
  return (
    <div className="min-h-screen py-8 pb-20 px-6">
      <div className="mx-auto max-w-2xl">
        {/* Header */}
        <div className="mb-14 animate-fade-in">
          <p className="kicker mb-3">Docs</p>
          <h1 className="text-3xl font-semibold tracking-tight text-[var(--ink)] mb-3">
            How EvoMind works
          </h1>
          <p className="text-base leading-relaxed" style={{ color: "var(--ink-tertiary)" }}>
            A personal knowledge base with hybrid RAG retrieval. Ingest your research, ask
            questions, and get cited answers grounded in what you know.
          </p>
        </div>

        {/* Steps */}
        <div className="space-y-6 animate-slide-up" style={{ animationDelay: "80ms" }}>
          {STEPS.map((step) => (
            <div key={step.number} className="surface-card p-6 group">
              <div className="flex items-start gap-5">
                <span
                  className="shrink-0 text-xs font-mono font-medium mt-0.5"
                  style={{ color: "var(--accent-warm)" }}
                >
                  {step.number}
                </span>
                <div>
                  <h2 className="text-base font-medium text-[var(--ink)] mb-2">{step.title}</h2>
                  <p className="text-sm leading-relaxed mb-3" style={{ color: "var(--ink-tertiary)" }}>
                    {step.description}
                  </p>
                  <Link
                    href={step.href}
                    className="inline-flex items-center gap-1.5 text-sm font-medium transition-colors duration-300"
                    style={{ color: "var(--ink-muted)" }}
                  >
                    {step.linkLabel}
                    <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                      <path d="M5 12h14M12 5l7 7-7 7" />
                    </svg>
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Architecture note */}
        <div className="mt-14 animate-slide-up" style={{ animationDelay: "160ms" }}>
          <h2 className="text-lg font-medium text-[var(--ink)] mb-4">Under the hood</h2>
          <div className="surface-card p-6">
            <ul className="space-y-3 text-sm leading-relaxed" style={{ color: "var(--ink-tertiary)" }}>
              <li className="flex gap-3">
                <span style={{ color: "var(--ink-muted)" }}>Storage</span>
                <span>SQLite with FTS5 full-text search + sqlite-vec for vector embeddings</span>
              </li>
              <li className="flex gap-3">
                <span style={{ color: "var(--ink-muted)" }}>Embeddings</span>
                <span>384-dimension vectors via fastembed (BAAI/bge-small-en-v1.5)</span>
              </li>
              <li className="flex gap-3">
                <span style={{ color: "var(--ink-muted)" }}>Retrieval</span>
                <span>Hybrid search — vector similarity fused with BM25 keyword matching</span>
              </li>
              <li className="flex gap-3">
                <span style={{ color: "var(--ink-muted)" }}>Generation</span>
                <span>Claude Sonnet via AWS Bedrock, grounded in retrieved context</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
