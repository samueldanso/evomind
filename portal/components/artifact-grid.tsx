"use client";

import { ArtifactCard } from "@/components/artifact-card";
import type { Artifact } from "@/lib/types";

export function ArtifactGrid({ artifacts }: { artifacts: Artifact[] }) {
  if (artifacts.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center py-24 text-muted-foreground">
        No research artifacts yet.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {artifacts.map((artifact) => (
        <ArtifactCard key={artifact.id} artifact={artifact} />
      ))}
    </div>
  );
}
