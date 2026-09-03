"use client";

import { useState } from "react";
import Link from "next/link";
import { X } from "@phosphor-icons/react";

type IngestState = "idle" | "loading" | "success" | "error";

interface IngestResult {
  slug: string;
  title: string;
  chunks: number;
}

export function AddSourceDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [tags, setTags] = useState("");
  const [state, setState] = useState<IngestState>("idle");
  const [result, setResult] = useState<IngestResult | null>(null);
  const [error, setError] = useState("");

  function handleReset() {
    setTitle("");
    setText("");
    setTags("");
    setState("idle");
    setResult(null);
    setError("");
  }

  function handleClose() {
    handleReset();
    onClose();
  }

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

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0"
        onClick={handleClose}
        onKeyDown={(e) => e.key === "Escape" && handleClose()}
        style={{ background: "rgba(0,0,0,0.6)", backdropFilter: "blur(8px)" }}
      />

      {/* Dialog */}
      <div
        className="relative w-full max-w-lg max-h-[85dvh] overflow-y-auto rounded-2xl p-6 animate-slide-up"
        style={{
          background: "var(--surface-1)",
          border: "1px solid var(--border-strong)",
          boxShadow: "0 24px 48px rgba(0,0,0,0.4)",
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold" style={{ color: "var(--ink)" }}>
            Add source
          </h2>
          <div className="flex items-center gap-2">
            <kbd
              className="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-xs font-mono"
              style={{
                background: "var(--surface-3)",
                color: "var(--ink-muted)",
                border: "1px solid var(--border-default)",
              }}
            >
              ESC
            </kbd>
            <button
              type="button"
              onClick={handleClose}
              className="p-1.5 rounded-lg transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] hover:bg-[var(--surface-2)]"
              style={{ color: "var(--ink-muted)" }}
            >
              <X size={16} weight="bold" />
            </button>
          </div>
        </div>

        {/* Success state */}
        {state === "success" && result ? (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-emerald-500/15 flex items-center justify-center">
                <svg
                  width={16}
                  height={16}
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#34d399"
                  strokeWidth={2.5}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M20 6 9 17l-5-5" />
                </svg>
              </div>
              <p className="text-sm" style={{ color: "var(--ink-secondary)" }}>
                <strong style={{ color: "var(--ink)" }}>{result.title}</strong> was chunked into{" "}
                {result.chunks} segment{result.chunks !== 1 ? "s" : ""} and embedded.
              </p>
            </div>
            <div className="flex gap-3">
              <Link
                href={`/wiki/${result.slug}`}
                className="btn-primary text-sm"
                onClick={handleClose}
              >
                View article
              </Link>
              <button type="button" onClick={handleReset} className="btn-secondary text-sm">
                Add another
              </button>
            </div>
          </div>
        ) : (
          /* Form */
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="dialog-title"
                className="block text-sm font-medium mb-1.5"
                style={{ color: "var(--ink-secondary)" }}
              >
                Title
              </label>
              <input
                id="dialog-title"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Retrieval-Augmented Generation"
                className="input-field"
                required
                disabled={state === "loading"}
                autoFocus
              />
            </div>

            <div>
              <label
                htmlFor="dialog-content"
                className="block text-sm font-medium mb-1.5"
                style={{ color: "var(--ink-secondary)" }}
              >
                Content
              </label>
              <textarea
                id="dialog-content"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Paste your research notes, article text, or any content..."
                className="input-field min-h-[160px] resize-y"
                required
                disabled={state === "loading"}
              />
            </div>

            <div>
              <label
                htmlFor="dialog-tags"
                className="block text-sm font-medium mb-1.5"
                style={{ color: "var(--ink-secondary)" }}
              >
                Tags
                <span className="ml-1.5 font-normal" style={{ color: "var(--ink-muted)" }}>
                  (comma-separated)
                </span>
              </label>
              <input
                id="dialog-tags"
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="e.g. rag, retrieval, llm"
                className="input-field"
                disabled={state === "loading"}
              />
            </div>

            {state === "error" && (
              <div
                className="rounded-xl p-3"
                style={{
                  background: "rgba(239,68,68,0.08)",
                  border: "1px solid rgba(239,68,68,0.2)",
                }}
              >
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={state === "loading" || !title.trim() || !text.trim()}
              className="btn-primary w-full disabled:opacity-40 disabled:pointer-events-none"
            >
              {state === "loading" ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <circle
                      cx={12}
                      cy={12}
                      r={10}
                      stroke="currentColor"
                      strokeWidth={3}
                      strokeLinecap="round"
                      className="opacity-25"
                    />
                    <path
                      d="M4 12a8 8 0 018-8"
                      stroke="currentColor"
                      strokeWidth={3}
                      strokeLinecap="round"
                    />
                  </svg>
                  Processing...
                </span>
              ) : (
                "Add to wiki"
              )}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
