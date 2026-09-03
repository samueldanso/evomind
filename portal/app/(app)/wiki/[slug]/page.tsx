"use client";

import { ArrowLeft, Calendar, Clock, Tag, Trash } from "@phosphor-icons/react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { Artifact } from "@/lib/types";
import { parseTags } from "@/lib/utils";

function estimateReadingTime(text: string): number {
  const words = text.split(/\s+/).length;
  return Math.max(1, Math.round(words / 200));
}

export default function WikiDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const router = useRouter();
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    fetch(`/api/artifacts/${slug}`)
      .then((res) => {
        if (!res.ok) {
          setNotFound(true);
          return null;
        }
        return res.json();
      })
      .then((data) => {
        if (data) setArtifact(data);
      })
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
  }, [slug]);

  async function handleDelete() {
    if (!confirm("Delete this article? This cannot be undone.")) return;
    setDeleting(true);
    try {
      const res = await fetch(`/api/artifacts/${slug}`, { method: "DELETE" });
      if (res.ok || res.status === 204) {
        router.push("/wiki");
      } else {
        alert("Failed to delete article.");
        setDeleting(false);
      }
    } catch {
      alert("Failed to delete article.");
      setDeleting(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen">
        <div className="mx-auto max-w-6xl px-6 py-8">
          <div className="text-sm text-center py-12" style={{ color: "var(--ink-muted)" }}>
            Loading...
          </div>
        </div>
      </div>
    );
  }

  if (notFound || !artifact) {
    return (
      <div className="min-h-screen">
        <div className="mx-auto max-w-6xl px-6 py-8">
          <nav className="mb-8">
            <Link
              href="/wiki"
              className="inline-flex items-center gap-1.5 text-sm transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] hover:text-[var(--ink)]"
              style={{ color: "var(--ink-muted)" }}
            >
              <ArrowLeft size={14} weight="bold" />
              Back to wiki
            </Link>
          </nav>
          <p className="text-sm text-center py-12" style={{ color: "var(--ink-muted)" }}>
            Article not found.
          </p>
        </div>
      </div>
    );
  }

  const tags = parseTags(artifact.tags);
  const date = artifact.created_at.slice(0, 10);
  const readTime = estimateReadingTime(artifact.summary ?? "");

  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-6xl px-6 py-8">
        {/* Breadcrumb */}
        <nav className="mb-8">
          <Link
            href="/wiki"
            className="inline-flex items-center gap-1.5 text-sm transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] hover:text-[var(--ink)]"
            style={{ color: "var(--ink-muted)" }}
          >
            <ArrowLeft size={14} weight="bold" />
            Back to wiki
          </Link>
        </nav>

        <div className="flex flex-col lg:flex-row gap-10">
          {/* Content */}
          <div className="flex-1 min-w-0">
            <header className="mb-8">
              <h1
                className="text-2xl sm:text-3xl font-semibold tracking-tight text-balance"
                style={{ color: "var(--ink)", letterSpacing: "-0.02em" }}
              >
                {artifact.title}
              </h1>

              {artifact.summary && (
                <p
                  className="mt-4 text-lg leading-relaxed font-medium text-pretty"
                  style={{ color: "var(--ink-tertiary)" }}
                >
                  {artifact.summary}
                </p>
              )}
            </header>

            <div className="surface-card p-8">
              <div className="wiki-prose">
                <p>{artifact.summary}</p>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <aside className="w-full lg:w-[280px] flex-shrink-0">
            <div className="lg:sticky lg:top-8 space-y-6">
              {/* Metadata card */}
              <div className="surface-card p-5 space-y-4">
                <h4
                  className="text-xs font-medium uppercase tracking-wider"
                  style={{ color: "var(--ink-muted)" }}
                >
                  Details
                </h4>

                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Calendar size={14} weight="bold" style={{ color: "var(--ink-faint)" }} />
                    <span className="text-sm" style={{ color: "var(--ink-tertiary)" }}>
                      {date}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock size={14} weight="bold" style={{ color: "var(--ink-faint)" }} />
                    <span className="text-sm" style={{ color: "var(--ink-tertiary)" }}>
                      {readTime} min read
                    </span>
                  </div>
                </div>

                {tags.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Tag size={14} weight="bold" style={{ color: "var(--ink-faint)" }} />
                      <span
                        className="text-xs font-medium uppercase tracking-wider"
                        style={{ color: "var(--ink-muted)" }}
                      >
                        Tags
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {tags.map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-0.5 rounded text-xs font-medium"
                          style={{
                            background: "var(--surface-2)",
                            color: "var(--ink-tertiary)",
                            border: "1px solid var(--border-default)",
                          }}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Delete button */}
              <button
                type="button"
                onClick={handleDelete}
                disabled={deleting}
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all duration-300 hover:bg-red-500/10 disabled:opacity-50 disabled:cursor-not-allowed w-full"
                style={{
                  color: "rgb(239, 68, 68)",
                  border: "1px solid rgba(239, 68, 68, 0.2)",
                }}
              >
                <Trash size={14} weight="bold" />
                {deleting ? "Deleting..." : "Delete article"}
              </button>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
