"use client";

import { useState } from "react";
import Link from "next/link";

type IngestState = "idle" | "loading" | "success" | "error";

interface IngestResult {
  slug: string;
  title: string;
  chunks: number;
}

export default function IngestPage() {
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [tags, setTags] = useState("");
  const [state, setState] = useState<IngestState>("idle");
  const [result, setResult] = useState<IngestResult | null>(null);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setState("loading");
    setError("");

    try {
      const res = await fetch("/api/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: title.trim(),
          text: text.trim(),
          tags: tags.trim(),
          topics: "",
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Ingest failed");
      }

      setResult(data);
      setState("success");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setState("error");
    }
  }

  function handleReset() {
    setTitle("");
    setText("");
    setTags("");
    setState("idle");
    setResult(null);
    setError("");
  }

  return (
    <div className="min-h-screen py-8 pb-20 px-6">
      <div className="mx-auto max-w-2xl">
        {/* Header */}
        <div className="mb-10 animate-fade-in">
          <p className="kicker mb-3">Ingest</p>
          <h1 className="text-3xl font-semibold tracking-tight text-[var(--ink)] mb-3">
            Add a source
          </h1>
          <p className="text-base leading-relaxed" style={{ color: "var(--ink-tertiary)" }}>
            Paste text, drop a URL, or add research notes. EvoMind chunks, embeds, and indexes it
            into your knowledge base.
          </p>
        </div>

        {/* Success state */}
        {state === "success" && result && (
          <div className="surface-card p-8 animate-slide-up">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 rounded-full bg-emerald-500/15 flex items-center justify-center">
                <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="#34d399" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 6 9 17l-5-5" />
                </svg>
              </div>
              <h2 className="text-lg font-medium text-[var(--ink)]">Source added</h2>
            </div>
            <p className="text-sm mb-1" style={{ color: "var(--ink-secondary)" }}>
              <strong>{result.title}</strong> was chunked into {result.chunks} segment{result.chunks !== 1 ? "s" : ""} and embedded.
            </p>
            <div className="flex gap-3 mt-6">
              <Link href={`/wiki/${result.slug}`} className="btn-primary text-sm">
                View article
              </Link>
              <button type="button" onClick={handleReset} className="btn-secondary text-sm">
                Add another
              </button>
            </div>
          </div>
        )}

        {/* Form */}
        {state !== "success" && (
          <form onSubmit={handleSubmit} className="space-y-5 animate-slide-up" style={{ animationDelay: "80ms" }}>
            {/* Title */}
            <div>
              <label htmlFor="title" className="block text-sm font-medium mb-2" style={{ color: "var(--ink-secondary)" }}>
                Title
              </label>
              <input
                id="title"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Retrieval-Augmented Generation"
                className="input-field"
                required
                disabled={state === "loading"}
              />
            </div>

            {/* Content */}
            <div>
              <label htmlFor="content" className="block text-sm font-medium mb-2" style={{ color: "var(--ink-secondary)" }}>
                Content
              </label>
              <textarea
                id="content"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Paste your research notes, article text, or any content you want to index..."
                className="input-field min-h-[220px] resize-y"
                required
                disabled={state === "loading"}
              />
            </div>

            {/* Tags */}
            <div>
              <label htmlFor="tags" className="block text-sm font-medium mb-2" style={{ color: "var(--ink-secondary)" }}>
                Tags
                <span className="ml-1.5 font-normal" style={{ color: "var(--ink-muted)" }}>(comma-separated)</span>
              </label>
              <input
                id="tags"
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="e.g. rag, retrieval, llm"
                className="input-field"
                disabled={state === "loading"}
              />
            </div>

            {/* Error */}
            {state === "error" && (
              <div className="rounded-xl p-4" style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)" }}>
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={state === "loading" || !title.trim() || !text.trim()}
              className="btn-primary w-full disabled:opacity-40 disabled:pointer-events-none"
            >
              {state === "loading" ? (
                <>
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <circle cx={12} cy={12} r={10} stroke="currentColor" strokeWidth={3} strokeLinecap="round" className="opacity-25" />
                    <path d="M4 12a8 8 0 018-8" stroke="currentColor" strokeWidth={3} strokeLinecap="round" />
                  </svg>
                  Processing...
                </>
              ) : (
                "Add to Wiki"
              )}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
