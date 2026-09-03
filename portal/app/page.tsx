import Link from "next/link";
import { ArrowRight, Search, Database, Shield, Layers, MessageSquare } from "lucide-react";

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
              Hybrid RAG Knowledge Base
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
                desc: "Vector search (sqlite-vec) fused with FTS5 full-text search via score-based merge. Neither alone covers the question space — hybrid retrieval combines semantic similarity with exact keyword matching for comprehensive recall.",
                Icon: Layers,
              },
              {
                title: "Cited Answers",
                desc: "Ask a question in natural language, get an answer grounded in your knowledge base with source citations. Every answer traces back to the chunks that informed it — no hallucination without attribution.",
                Icon: MessageSquare,
              },
              {
                title: "Embedding Pipeline",
                desc: "Sentence-boundary chunking with configurable overlap. Local ONNX embeddings via fastembed — no external API dependency for vector generation. Incremental and full rebuild modes with batched processing.",
                Icon: Database,
              },
              {
                title: "Eval-Gated Quality",
                desc: "Retrieval quality harness with curated test questions gates every change. No schema migration, no embedding model swap, no chunking adjustment ships without passing the eval. The eval is the contract.",
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
              "OpenRouter", "LLaMA 3.3", "fastembed",
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
