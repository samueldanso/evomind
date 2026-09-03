"use client";

import { useEffect, useState } from "react";
import { WikiGrid } from "@/components/wiki-grid";
import type { Artifact } from "@/lib/types";

export default function WikiPage() {
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/artifacts")
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setArtifacts(data))
      .catch(() => setArtifacts([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-6xl px-6 py-8">
        <header className="mb-10">
          <span className="kicker">{loading ? "\u00A0" : `${artifacts.length} artifacts`}</span>
          <h1 className="section-title mt-2">Knowledge base</h1>
          <p className="mt-2 text-sm" style={{ color: "var(--ink-muted)" }}>
            Research notes and articles from your knowledge base.
          </p>
        </header>
        {loading ? (
          <div className="text-sm text-center py-12" style={{ color: "var(--ink-muted)" }}>
            Loading artifacts...
          </div>
        ) : (
          <WikiGrid artifacts={artifacts} />
        )}
      </div>
    </div>
  );
}
