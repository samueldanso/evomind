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
