"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { ArrowRight, MagnifyingGlass, Database, ShieldCheck, Stack, ChatCircle } from "@phosphor-icons/react";

function useScrollReveal() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = ref.current;
    if (!container) return;

    const elements = container.querySelectorAll(".reveal");
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add("revealed");
            observer.unobserve(entry.target);
          }
        }
      },
      { threshold: 0.15, rootMargin: "0px 0px -40px 0px" },
    );

    for (const el of elements) {
      observer.observe(el);
    }

    return () => observer.disconnect();
  }, []);

  return ref;
}

export default function Home() {
  const containerRef = useScrollReveal();

  return (
    <div ref={containerRef} className="min-h-screen bg-black">
      {/* Hero */}
      <section className="relative min-h-[100dvh] flex items-center justify-center px-6 overflow-hidden">
        {/* Subtle warm ambient glow */}
        <div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[500px] pointer-events-none"
          style={{
            background: "radial-gradient(ellipse at center, rgba(212,165,116,0.06) 0%, transparent 70%)",
          }}
        />

        <div className="relative z-10 max-w-3xl mx-auto text-center">
          <div className="reveal mb-6">
            <span className="kicker inline-flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#d4a574]" />
              Hybrid RAG knowledge base
            </span>
          </div>

          <h1 className="reveal text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-medium tracking-tight text-balance text-gradient" style={{ lineHeight: 1.05, letterSpacing: "-0.03em" }}>
            Your research,
            <br />
            compounding over time
          </h1>

          <p className="reveal mt-6 text-base sm:text-lg max-w-xl mx-auto text-pretty" style={{ color: "rgba(245,245,244,0.5)", lineHeight: 1.6 }}>
            Ingest web research. Embed it into a hybrid vector + full-text search index.
            Ask questions and get cited answers grounded in your own knowledge base.
          </p>

          <div className="reveal mt-10 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link href="/wiki" className="btn-primary group">
              <span>Explore the wiki</span>
              <ArrowRight
                size={14}
                weight="bold"
                className="opacity-0 -ml-2 group-hover:opacity-100 group-hover:ml-0 transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)]"
              />
            </Link>
            <Link href="/search" className="btn-secondary">
              <MagnifyingGlass size={14} weight="bold" />
              <span>Ask a question</span>
            </Link>
          </div>
        </div>
      </section>

      {/* Features — asymmetric: large left card + two stacked right */}
      <section className="px-6 py-24 border-t border-[rgba(255,255,255,0.04)]">
        <div className="max-w-6xl mx-auto">
          <div className="mb-16 max-w-lg reveal">
            <span className="kicker">Under the hood</span>
            <h2 className="section-title mt-2 text-balance">Built with engineering depth</h2>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 reveal-stagger">
            {/* Large feature card */}
            <div className="reveal lg:col-span-7 surface-card p-8">
              <div
                className="w-10 h-10 rounded-lg flex items-center justify-center mb-4"
                style={{ background: "rgba(212,165,116,0.1)", color: "#d4a574" }}
              >
                <Stack size={20} weight="duotone" />
              </div>
              <h3 className="text-lg font-medium mb-3" style={{ color: "#f5f5f4" }}>
                Hybrid RAG retrieval
              </h3>
              <p className="text-sm leading-relaxed max-w-lg" style={{ color: "rgba(245,245,244,0.5)" }}>
                Vector search (sqlite-vec) fused with FTS5 full-text search via score-based merge. Neither alone covers the question space — hybrid retrieval combines semantic similarity with exact keyword matching for comprehensive recall.
              </p>
            </div>

            {/* Two stacked cards */}
            <div className="lg:col-span-5 flex flex-col gap-4">
              <div className="reveal surface-card p-6 flex-1">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center mb-4"
                  style={{ background: "rgba(212,165,116,0.1)", color: "#d4a574" }}
                >
                  <ChatCircle size={20} weight="duotone" />
                </div>
                <h3 className="text-base font-medium mb-2" style={{ color: "#f5f5f4" }}>
                  Cited answers
                </h3>
                <p className="text-sm leading-relaxed" style={{ color: "rgba(245,245,244,0.5)" }}>
                  Ask a question in natural language, get an answer grounded in your knowledge base with source citations. Every answer traces back to the chunks that informed it.
                </p>
              </div>

              <div className="reveal surface-card p-6 flex-1">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center mb-4"
                  style={{ background: "rgba(212,165,116,0.1)", color: "#d4a574" }}
                >
                  <Database size={20} weight="duotone" />
                </div>
                <h3 className="text-base font-medium mb-2" style={{ color: "#f5f5f4" }}>
                  Embedding pipeline
                </h3>
                <p className="text-sm leading-relaxed" style={{ color: "rgba(245,245,244,0.5)" }}>
                  Sentence-boundary chunking with configurable overlap. Local ONNX embeddings via fastembed — no external API dependency for vector generation.
                </p>
              </div>
            </div>

            {/* Full-width bottom card */}
            <div className="reveal lg:col-span-12 surface-card p-6">
              <div className="flex flex-col sm:flex-row sm:items-start gap-4">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
                  style={{ background: "rgba(212,165,116,0.1)", color: "#d4a574" }}
                >
                  <ShieldCheck size={20} weight="duotone" />
                </div>
                <div>
                  <h3 className="text-base font-medium mb-2" style={{ color: "#f5f5f4" }}>
                    Eval-gated quality
                  </h3>
                  <p className="text-sm leading-relaxed max-w-2xl" style={{ color: "rgba(245,245,244,0.5)" }}>
                    Retrieval quality harness with curated test questions gates every change. No schema migration, no embedding model swap, no chunking adjustment ships without passing the eval. The eval is the contract.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Tech stack */}
      <section className="px-6 py-16 border-t border-[rgba(255,255,255,0.04)]">
        <div className="max-w-3xl mx-auto text-center reveal">
          <span className="kicker">Stack</span>
          <div className="mt-4 flex flex-wrap items-center justify-center gap-3">
            {[
              "Python", "FastAPI", "SQLite", "sqlite-vec", "FTS5",
              "OpenRouter", "Gemma 4", "fastembed",
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

      {/* Tagline — no italic, use weight + muted color */}
      <section className="px-6 py-24 border-t border-[rgba(255,255,255,0.04)]">
        <div className="max-w-3xl mx-auto text-center reveal">
          <p className="text-xl font-medium text-balance" style={{ color: "rgba(245,245,244,0.5)" }}>
            &ldquo;The goal isn&apos;t to remember everything.
            <br className="hidden sm:inline" />
            It&apos;s to never lose what matters.&rdquo;
          </p>
        </div>
      </section>
    </div>
  );
}
