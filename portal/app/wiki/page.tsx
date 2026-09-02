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
      <div className="mx-auto max-w-6xl px-6 py-12">
        <header className="mb-10">
          <span className="kicker">{artifacts.length} artifacts</span>
          <h1 className="section-title mt-2">Knowledge Base</h1>
          <p className="mt-2 text-sm" style={{ color: "rgba(245,245,244,0.45)" }}>
            Research artifacts built by agents and ingested from web sources.
          </p>
        </header>
        <WikiGrid artifacts={artifacts} />
      </div>
    </div>
  );
}
