import { ArtifactGrid } from "@/components/artifact-grid";
import { getDb, resetDb } from "@/lib/db";
import type { Artifact } from "@/lib/types";

function fetchArtifacts(): Artifact[] {
  try {
    const db = getDb();
    return db
      .prepare("SELECT * FROM artifacts ORDER BY created_at DESC")
      .all() as Artifact[];
  } catch (err) {
    // Reset cached connection so next request retries (e.g. DB created after server start)
    resetDb();
    console.error("[page] failed to load artifacts:", err);
    return [];
  }
}

export default async function Home() {
  const artifacts = fetchArtifacts();

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <header className="mb-10">
          <h1 className="text-3xl font-bold tracking-tight">EvoResearch</h1>
          <p className="mt-1 text-muted-foreground">
            Samuel&apos;s living research corpus
          </p>
        </header>
        <ArtifactGrid artifacts={artifacts} />
      </div>
    </div>
  );
}
