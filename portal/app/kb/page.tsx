import { ArtifactGrid } from "@/components/artifact-grid";
import { getDb, resetDb } from "@/lib/db";
import type { Artifact } from "@/lib/types";

function fetchArtifacts(): Artifact[] {
  try {
    const db = getDb();
    return db.prepare("SELECT * FROM artifacts ORDER BY created_at DESC").all() as Artifact[];
  } catch (err) {
    resetDb();
    console.error("[kb] failed to load artifacts:", err);
    return [];
  }
}

export default async function KBPage() {
  const artifacts = fetchArtifacts();

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <header className="mb-10">
          <h1 className="text-3xl font-bold tracking-tight">Knowledge Base</h1>
          <p className="mt-1 text-muted-foreground">Research artifacts built by agents</p>
        </header>
        <ArtifactGrid artifacts={artifacts} />
      </div>
    </div>
  );
}
