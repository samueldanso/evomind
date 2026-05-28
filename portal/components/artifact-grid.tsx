"use client";

import { useState } from "react";
import { ArtifactCard } from "@/components/artifact-card";
import { Badge } from "@/components/ui/badge";
import type { Artifact } from "@/lib/types";

function parseTags(tags: string): string[] {
  return tags
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean);
}

function uniqueTags(artifacts: Artifact[]): string[] {
  const seen = new Set<string>();
  for (const a of artifacts) {
    for (const tag of parseTags(a.tags)) {
      seen.add(tag);
    }
  }
  return Array.from(seen).sort();
}

export function ArtifactGrid({ artifacts }: { artifacts: Artifact[] }) {
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set());

  const allTags = uniqueTags(artifacts);

  function toggleTag(tag: string) {
    setSelectedTags((prev) => {
      const next = new Set(prev);
      if (next.has(tag)) {
        next.delete(tag);
      } else {
        next.add(tag);
      }
      return next;
    });
  }

  const filtered =
    selectedTags.size === 0
      ? artifacts
      : artifacts.filter((a) =>
          parseTags(a.tags).some((tag) => selectedTags.has(tag)),
        );

  if (artifacts.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center py-24 text-muted-foreground">
        No research artifacts yet.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {allTags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {allTags.map((tag) => (
            <button key={tag} type="button" onClick={() => toggleTag(tag)}>
              <Badge
                variant={selectedTags.has(tag) ? "default" : "outline"}
                className="cursor-pointer"
              >
                {tag}
              </Badge>
            </button>
          ))}
          {selectedTags.size > 0 && (
            <button
              type="button"
              onClick={() => setSelectedTags(new Set())}
            >
              <Badge variant="ghost" className="cursor-pointer">
                Clear
              </Badge>
            </button>
          )}
        </div>
      )}

      {filtered.length === 0 ? (
        <div className="flex items-center justify-center py-16 text-muted-foreground">
          No artifacts match the selected tags.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((artifact) => (
            <ArtifactCard key={artifact.id} artifact={artifact} />
          ))}
        </div>
      )}
    </div>
  );
}
