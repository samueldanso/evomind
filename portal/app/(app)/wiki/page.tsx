import { WikiGrid } from "@/components/wiki-grid";
import { getDb, resetDb } from "@/lib/db";
import type { Artifact } from "@/lib/types";

function fetchArtifacts(): Artifact[] {
  try {
    const db = getDb();
    return db.prepare("SELECT * FROM artifacts ORDER BY created_at DESC").all() as Artifact[];
  } catch (err) {
    resetDb();
    console.error("[wiki] failed to load artifacts:", err);
    return [];
  }
}

export default async function WikiPage() {
  const artifacts = fetchArtifacts();

  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-6xl px-6 py-8">
        <header className="mb-10">
          <span className="kicker">{artifacts.length} artifacts</span>
          <h1 className="section-title mt-2">Knowledge base</h1>
          <p className="mt-2 text-sm" style={{ color: "var(--ink-muted)" }}>
            Research notes and articles from your knowledge base.
          </p>
        </header>
        <WikiGrid artifacts={artifacts} />
      </div>
    </div>
  );
}
