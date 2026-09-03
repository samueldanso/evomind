"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import { Globe, TextAa, FileArrowUp, SpinnerGap, Check } from "@phosphor-icons/react";

type IngestMode = "text" | "url" | "file";
type IngestState = "idle" | "fetching" | "loading" | "success" | "error";

interface IngestResult {
  slug: string;
  title: string;
  chunks: number;
}

export default function IngestPage() {
  const [mode, setMode] = useState<IngestMode>("text");
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [tags, setTags] = useState("");
  const [state, setState] = useState<IngestState>("idle");
  const [result, setResult] = useState<IngestResult | null>(null);
  const [error, setError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState("");

  async function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setFileName(file.name);
    setState("fetching");
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Upload failed");
      }

      setText(data.text);
      if (!title.trim()) setTitle(data.title);
      setState("idle");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to process file");
      setState("error");
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (mode === "url" && url.trim()) {
      setState("fetching");
      setError("");

      try {
        const res = await fetch("/api/ingest", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            url: url.trim(),
            title: title.trim() || "",
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
      return;
    }

    // Text mode (or file mode after extraction)
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
    setUrl("");
    setTags("");
    setFileName("");
    setState("idle");
    setResult(null);
    setError("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  const isSubmitDisabled =
    state === "loading" ||
    state === "fetching" ||
    (mode === "url" ? !url.trim() : !title.trim() || !text.trim());

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
            Paste text, drop a URL, or upload a file. EvoMind chunks, embeds, and indexes it
            into your knowledge base.
          </p>
        </div>

        {/* Success state */}
        {state === "success" && result && (
          <div className="surface-card p-8 animate-slide-up">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 rounded-full bg-emerald-500/15 flex items-center justify-center">
                <Check size={16} weight="bold" className="text-emerald-400" />
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
            {/* Mode tabs */}
            <div
              className="flex gap-1 p-1 rounded-full w-fit"
              style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)" }}
            >
              <ModeTab active={mode === "text"} onClick={() => setMode("text")}>
                <TextAa size={14} weight="bold" />
                Text
              </ModeTab>
              <ModeTab active={mode === "url"} onClick={() => setMode("url")}>
                <Globe size={14} weight="bold" />
                URL
              </ModeTab>
              <ModeTab active={mode === "file"} onClick={() => setMode("file")}>
                <FileArrowUp size={14} weight="bold" />
                File
              </ModeTab>
            </div>

            {/* URL input */}
            {mode === "url" && (
              <div>
                <label htmlFor="url" className="block text-sm font-medium mb-2" style={{ color: "var(--ink-secondary)" }}>
                  URL
                </label>
                <input
                  id="url"
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com/article"
                  className="input-field"
                  required
                  disabled={state === "fetching" || state === "loading"}
                />
              </div>
            )}

            {/* File input */}
            {mode === "file" && (
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: "var(--ink-secondary)" }}>
                  Upload file
                  <span className="ml-1.5 font-normal" style={{ color: "var(--ink-muted)" }}>(.pdf, .docx, .txt, .md)</span>
                </label>
                <div
                  className="relative surface-card p-6 flex flex-col items-center gap-3 cursor-pointer hover:border-[var(--border-strong)]"
                  onClick={() => fileInputRef.current?.click()}
                  onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") fileInputRef.current?.click(); }}
                  role="button"
                  tabIndex={0}
                >
                  {state === "fetching" ? (
                    <>
                      <SpinnerGap size={20} className="animate-spin" style={{ color: "var(--accent-warm)" }} />
                      <span className="text-sm" style={{ color: "var(--ink-tertiary)" }}>Extracting text from {fileName}...</span>
                    </>
                  ) : fileName ? (
                    <>
                      <Check size={20} weight="bold" className="text-emerald-400" />
                      <span className="text-sm" style={{ color: "var(--ink-secondary)" }}>{fileName}</span>
                      <span className="text-xs" style={{ color: "var(--ink-muted)" }}>Text extracted. Click to choose a different file.</span>
                    </>
                  ) : (
                    <>
                      <FileArrowUp size={24} weight="duotone" style={{ color: "var(--ink-muted)" }} />
                      <span className="text-sm" style={{ color: "var(--ink-tertiary)" }}>Click to select a file</span>
                    </>
                  )}
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.docx,.txt,.md"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                </div>
              </div>
            )}

            {/* Title */}
            <div>
              <label htmlFor="title" className="block text-sm font-medium mb-2" style={{ color: "var(--ink-secondary)" }}>
                Title
                {mode === "url" && (
                  <span className="ml-1.5 font-normal" style={{ color: "var(--ink-muted)" }}>(optional — auto-detected from page)</span>
                )}
              </label>
              <input
                id="title"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Retrieval-Augmented Generation"
                className="input-field"
                required={mode !== "url"}
                disabled={state === "fetching" || state === "loading"}
              />
            </div>

            {/* Content — shown for text and file modes */}
            {mode !== "url" && (
              <div>
                <label htmlFor="content" className="block text-sm font-medium mb-2" style={{ color: "var(--ink-secondary)" }}>
                  Content
                </label>
                <textarea
                  id="content"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder={mode === "file" ? "File content will appear here after upload..." : "Paste your research notes, article text, or any content you want to index..."}
                  className="input-field min-h-[220px] resize-y"
                  required
                  disabled={state === "fetching" || state === "loading"}
                />
              </div>
            )}

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
                disabled={state === "fetching" || state === "loading"}
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
              disabled={isSubmitDisabled}
              className="btn-primary w-full disabled:opacity-40 disabled:pointer-events-none"
            >
              {state === "fetching" ? (
                <>
                  <SpinnerGap size={16} className="animate-spin" />
                  Fetching...
                </>
              ) : state === "loading" ? (
                <>
                  <SpinnerGap size={16} className="animate-spin" />
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

function ModeTab({
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
