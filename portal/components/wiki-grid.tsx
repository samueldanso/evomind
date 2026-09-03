"use client";

import { useEffect, useRef, useState } from "react";
import { MagnifyingGlass } from "@phosphor-icons/react";
import { WikiCard } from "@/components/wiki-card";
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

export function WikiGrid({ artifacts }: { artifacts: Artifact[] }) {
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Artifact[] | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    abortRef.current?.abort();

    const q = searchQuery.trim();
    if (!q) {
      setSearchResults(null);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      const controller = new AbortController();
      abortRef.current = controller;
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`, {
          signal: controller.signal,
        });
        if (!res.ok) {
          setSearchResults([]);
          return;
        }
        const data = (await res.json()) as Artifact[];
        setSearchResults(data);
      } catch (err) {
        if (err instanceof Error && err.name === "AbortError") return;
        setSearchResults([]);
      }
    }, 300);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      abortRef.current?.abort();
    };
  }, [searchQuery]);

  const isSearchActive = searchResults !== null;
  const baseList = isSearchActive ? searchResults : artifacts;
  const allTags = uniqueTags(artifacts);

  function toggleTag(tag: string) {
    setSelectedTags((prev) => {
      const next = new Set(prev);
      if (next.has(tag)) next.delete(tag);
      else next.add(tag);
      return next;
    });
  }

  const displayed =
    !isSearchActive && selectedTags.size > 0
      ? baseList.filter((a) => parseTags(a.tags).some((tag) => selectedTags.has(tag)))
      : baseList;

  return (
    <div className="flex flex-col gap-6">
      {/* Search */}
      <div className="relative max-w-md">
        <MagnifyingGlass
          size={16}
          weight="bold"
          className="absolute left-4 top-1/2 -translate-y-1/2"
          style={{ color: "var(--ink-faint)" }}
        />
        <input
          type="text"
          placeholder="Search research…"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="input-field pl-11"
        />
      </div>

      {/* Tag filters */}
      {!isSearchActive && allTags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {allTags.map((tag) => {
            const active = selectedTags.has(tag);
            return (
              <button
                key={tag}
                type="button"
                onClick={() => toggleTag(tag)}
                className="px-3 py-1 rounded-full text-xs font-medium transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)]"
                style={{
                  background: active ? "rgba(212,165,116,0.15)" : "rgba(255,255,255,0.04)",
                  border: `1px solid ${active ? "rgba(212,165,116,0.3)" : "rgba(255,255,255,0.08)"}`,
                  color: active ? "#d4a574" : "rgba(245,245,244,0.5)",
                }}
              >
                {tag}
              </button>
            );
          })}
          {selectedTags.size > 0 && (
            <button
              type="button"
              onClick={() => setSelectedTags(new Set())}
              className="px-3 py-1 rounded-full text-xs font-medium text-[var(--ink-muted)] hover:text-[var(--ink-tertiary)] transition-colors"
            >
              Clear
            </button>
          )}
        </div>
      )}

      {/* Grid */}
      {displayed.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <p className="text-sm" style={{ color: "var(--ink-muted)" }}>
            {isSearchActive
              ? `No results for "${searchQuery.trim()}".`
              : artifacts.length === 0
                ? "No research artifacts yet."
                : "No artifacts match the selected tags."}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {displayed.map((artifact) => (
            <WikiCard key={artifact.id} artifact={artifact} />
          ))}
        </div>
      )}
    </div>
  );
}
