"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { MagnifyingGlass, Sparkle, SpinnerGap, PaperPlaneTilt, ChatCircle } from "@phosphor-icons/react";
import { type ChatResponse, type ChatSource, chat } from "@/lib/chat";
import type { Artifact } from "@/lib/types";

type Tab = "ask" | "search";

const SUGGESTED_QUESTIONS = [
  "How does hybrid search work?",
  "What is retrieval-augmented generation?",
  "How do embedding models compare?",
  "What chunking strategies exist for retrieval?",
];

export default function SearchPage() {
  const [activeTab, setActiveTab] = useState<Tab>("ask");

  return (
    <div className="min-h-screen pt-20">
      <div className="mx-auto max-w-4xl px-6 py-12">
        {/* Tab switcher */}
        <div className="flex gap-1 mb-8 p-1 rounded-full w-fit" style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)" }}>
          <TabButton active={activeTab === "ask"} onClick={() => setActiveTab("ask")}>
            <Sparkle size={14} weight="fill" />
            Ask AI
          </TabButton>
          <TabButton active={activeTab === "search"} onClick={() => setActiveTab("search")}>
            <MagnifyingGlass size={14} weight="bold" />
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
      className="flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-medium transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)]"
      style={{
        background: active ? "rgba(255,255,255,0.08)" : "transparent",
        color: active ? "#f5f5f4" : "rgba(245,245,244,0.45)",
      }}
    >
      {children}
    </button>
  );
}

/* -- Ask AI Tab -- */

interface QAPair {
  question: string;
  answer: string;
  sources: ChatSource[];
}

function AskAITab() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<QAPair[]>([]);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, loading]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed || loading) return;

    setLoading(true);
    setError(null);
    setQuery("");

    try {
      const response = await chat(trimmed);
      setHistory((prev) => [
        ...prev,
        { question: trimmed, answer: response.answer, sources: response.sources },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get answer");
    } finally {
      setLoading(false);
    }
  }

  function handleSuggestion(q: string) {
    setQuery(q);
  }

  return (
    <div className="flex flex-col" style={{ minHeight: "calc(100vh - 220px)" }}>
      {/* Chat area */}
      <div className="flex-1 space-y-6 pb-6">
        {/* Empty state */}
        {history.length === 0 && !loading && !error && (
          <div className="flex flex-col items-center justify-center py-16">
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center mb-6"
              style={{ background: "rgba(212,165,116,0.1)" }}
            >
              <ChatCircle size={24} weight="duotone" style={{ color: "#d4a574" }} />
            </div>
            <h2 className="text-lg font-medium mb-2" style={{ color: "#f5f5f4" }}>
              Ask your knowledge base
            </h2>
            <p className="text-sm mb-8 text-center max-w-md" style={{ color: "rgba(245,245,244,0.4)" }}>
              Get cited answers grounded in your research corpus using hybrid RAG retrieval.
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {SUGGESTED_QUESTIONS.map((q) => (
                <button
                  key={q}
                  type="button"
                  onClick={() => handleSuggestion(q)}
                  className="px-3 py-1.5 rounded-lg text-xs transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] hover:border-[rgba(212,165,116,0.3)] hover:text-[#d4a574]"
                  style={{
                    background: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(255,255,255,0.08)",
                    color: "rgba(245,245,244,0.5)",
                  }}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Q&A pairs */}
        {history.map((pair, i) => (
          <div key={`qa-${pair.question.slice(0, 20)}-${i}`} className="space-y-4">
            {/* Question */}
            <div className="flex justify-end">
              <div
                className="max-w-[80%] px-4 py-3 rounded-2xl rounded-br-md text-sm"
                style={{
                  background: "rgba(212,165,116,0.12)",
                  color: "#f5f5f4",
                }}
              >
                {pair.question}
              </div>
            </div>

            {/* Answer */}
            <div className="flex justify-start">
              <div className="max-w-full space-y-4">
                <div className="surface-card p-5">
                  <div className="wiki-prose text-sm leading-relaxed">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{pair.answer}</ReactMarkdown>
                  </div>
                </div>

                {/* Sources */}
                {pair.sources.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {pair.sources.map((source) => (
                      <SourceChip key={`${source.slug}-${i}`} source={source} />
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {/* Loading */}
        {loading && (
          <div className="flex justify-start">
            <div className="surface-card px-5 py-4 flex items-center gap-3">
              <SpinnerGap size={14} className="animate-spin" style={{ color: "#d4a574" }} />
              <span className="text-sm" style={{ color: "rgba(245,245,244,0.5)" }}>
                Searching corpus and generating answer...
              </span>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div
            className="p-4 rounded-xl text-sm"
            style={{
              background: "rgba(239,68,68,0.08)",
              border: "1px solid rgba(239,68,68,0.2)",
              color: "#fca5a5",
            }}
          >
            {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input — sticky at bottom */}
      <div
        className="sticky bottom-0 pt-4 pb-2"
        style={{ background: "linear-gradient(transparent, #000000 20%)" }}
      >
        <form onSubmit={handleSubmit} className="flex gap-3">
          <div className="relative flex-1">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask anything about your research..."
              disabled={loading}
              className="input-field pr-4"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="btn-primary disabled:opacity-40 disabled:cursor-not-allowed px-4"
          >
            {loading ? <SpinnerGap size={16} className="animate-spin" /> : <PaperPlaneTilt size={16} weight="fill" />}
          </button>
        </form>
      </div>
    </div>
  );
}

function SourceChip({ source }: { source: ChatSource }) {
  const matchColors: Record<string, string> = {
    vector: "#C7B8FF",
    vec: "#C7B8FF",
    fts: "#7BD0E8",
    hybrid: "#d4a574",
  };
  const color = matchColors[source.match_type] ?? "rgba(245,245,244,0.4)";

  return (
    <Link href={`/wiki/${source.slug}`}>
      <span
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] hover:opacity-80"
        style={{
          background: `${color}10`,
          border: `1px solid ${color}25`,
          color,
        }}
      >
        <span className="truncate max-w-[180px]">{source.title}</span>
        <span className="font-mono opacity-60">{source.score.toFixed(2)}</span>
      </span>
    </Link>
  );
}

/* -- Search Tab -- */

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
        <MagnifyingGlass
          size={16}
          weight="bold"
          className="absolute left-4 top-1/2 -translate-y-1/2"
          style={{ color: "rgba(245,245,244,0.3)" }}
        />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by keyword..."
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
                      className="text-sm font-medium group-hover:text-[#f5f5f4] transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)]"
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
