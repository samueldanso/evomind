"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import {
  ArrowRight,
  MagnifyingGlass,
  Upload,
  ShieldCheck,
  Stack,
  ChatCircle,
} from "@phosphor-icons/react";

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
      { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
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
    <div ref={containerRef} className="min-h-screen bg-[var(--background)]">
      {/* Hero */}
      <section className="relative min-h-[100dvh] flex items-center justify-center px-6 overflow-hidden">
        {/* Smooth warm ambient background */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse 80% 60% at 50% 40%, rgba(212,165,116,0.08) 0%, rgba(212,165,116,0.03) 40%, transparent 70%)",
          }}
        />

        <div className="relative z-10 max-w-3xl mx-auto text-center">
          <div className="reveal mb-6">
            <span className="kicker inline-flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#d4a574]" />
              Personal knowledge base
            </span>
          </div>

          <h1
            className="reveal text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-medium tracking-tight text-balance text-gradient"
            style={{ lineHeight: 1.05, letterSpacing: "-0.03em" }}
          >
            Remember everything
            <br />
            you&apos;ve ever read
          </h1>

          <p
            className="reveal mt-6 text-base sm:text-lg max-w-xl mx-auto text-pretty"
            style={{ color: "var(--ink-tertiary)", lineHeight: 1.6 }}
          >
            Drop in articles, PDFs, or research notes. EvoMind chunks, embeds, and indexes them —
            then answers your questions with citations.
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
            <span className="kicker">How it works</span>
            <h2 className="section-title mt-2 text-balance">Ingest. Search. Understand.</h2>
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
              <h3 className="text-lg font-medium mb-3" style={{ color: "var(--ink)" }}>
                Hybrid search
              </h3>
              <p
                className="text-sm leading-relaxed max-w-lg"
                style={{ color: "var(--ink-tertiary)" }}
              >
                Every query runs two search strategies in parallel — semantic vector similarity and
                full-text keyword matching — then fuses the results. You get the precision of exact
                terms and the recall of meaning.
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
                <h3 className="text-base font-medium mb-2" style={{ color: "var(--ink)" }}>
                  Cited answers
                </h3>
                <p className="text-sm leading-relaxed" style={{ color: "var(--ink-tertiary)" }}>
                  Ask a question, get an answer grounded in your sources with inline citations. No
                  hallucination without attribution — every claim traces back to what you ingested.
                </p>
              </div>

              <div className="reveal surface-card p-6 flex-1">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center mb-4"
                  style={{ background: "rgba(212,165,116,0.1)", color: "#d4a574" }}
                >
                  <Upload size={20} weight="duotone" />
                </div>
                <h3 className="text-base font-medium mb-2" style={{ color: "var(--ink)" }}>
                  Any source, any format
                </h3>
                <p className="text-sm leading-relaxed" style={{ color: "var(--ink-tertiary)" }}>
                  Paste text, drop a URL, or upload a PDF. EvoMind extracts content, splits it into
                  chunks, and embeds it locally — no data leaves your pipeline.
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
                  <h3 className="text-base font-medium mb-2" style={{ color: "var(--ink)" }}>
                    Quality you can measure
                  </h3>
                  <p
                    className="text-sm leading-relaxed max-w-2xl"
                    style={{ color: "var(--ink-tertiary)" }}
                  >
                    A retrieval eval harness runs on every change to the system. If search quality
                    drops, the change doesn&apos;t ship. Your knowledge base stays reliable as it
                    grows.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Tagline — no italic, use weight + muted color */}
      <section className="px-6 py-24 border-t border-[rgba(255,255,255,0.04)]">
        <div className="max-w-3xl mx-auto text-center reveal">
          <p
            className="text-xl font-medium text-balance"
            style={{ color: "var(--ink-tertiary)" }}
          >
            &ldquo;The goal isn&apos;t to remember everything.
            <br className="hidden sm:inline" />
            It&apos;s to never lose what matters.&rdquo;
          </p>
        </div>
      </section>
    </div>
  );
}
