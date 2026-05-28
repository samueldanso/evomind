"use client";

import { useEffect, useRef, useState } from "react";
import { ArtifactCard } from "@/components/artifact-card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import type { Artifact } from "@/lib/types";
import { parseTags } from "@/lib/utils";

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
  const [searchQuery, setSearchQuery] = useState("");
  // null = search inactive (show all); array = search results
  const [searchResults, setSearchResults] = useState<Artifact[] | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    const q = searchQuery.trim();
    if (!q) {
      setSearchResults(null);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      try {
        const res = await fetch(
          `/api/search?q=${encodeURIComponent(q)}`,
        );
        if (!res.ok) {
          console.error(`[search] API error ${res.status} for query: ${q}`);
          setSearchResults([]);
          return;
        }
        const data = (await res.json()) as Artifact[];
        setSearchResults(data);
      } catch (err) {
        console.error("[search] fetch failed:", err);
        setSearchResults([]);
      }
    }, 300);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [searchQuery]);

  const isSearchActive = searchResults !== null;
  const baseList = isSearchActive ? searchResults : artifacts;

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

  const displayed =
    !isSearchActive && selectedTags.size > 0
      ? baseList.filter((a) =>
          parseTags(a.tags).some((tag) => selectedTags.has(tag)),
        )
      : baseList;

  if (artifacts.length === 0) {
    return (
      <div className="flex flex-col gap-6">
        <Input
          placeholder="Search research…"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="max-w-sm"
        />
        <div className="flex flex-1 items-center justify-center py-24 text-muted-foreground">
          No research artifacts yet.
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <Input
        placeholder="Search research…"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        className="max-w-sm"
      />

      {!isSearchActive && allTags.length > 0 && (
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

      {displayed.length === 0 ? (
        <div className="flex items-center justify-center py-16 text-muted-foreground">
          {isSearchActive
            ? `No results for "${searchQuery.trim()}".`
            : "No artifacts match the selected tags."}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {displayed.map((artifact) => (
            <ArtifactCard key={artifact.id} artifact={artifact} />
          ))}
        </div>
      )}
    </div>
  );
}
