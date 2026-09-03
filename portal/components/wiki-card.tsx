import Link from "next/link";
import type { Artifact } from "@/lib/types";
import { parseTags } from "@/lib/utils";

const TYPE_COLORS: Record<string, string> = {
  concept: "#C7B8FF",
  person: "#9BDCAA",
  place: "#F4C77B",
  event: "#F49B9B",
  tool: "#7BD0E8",
  organization: "#B4B0F0",
};

function TypeBadge({ type }: { type: string }) {
  const color = TYPE_COLORS[type.toLowerCase()] ?? "var(--ink-muted)";
  return (
    <span
      className="inline-block px-2 py-0.5 rounded-full text-xs font-medium uppercase tracking-wider"
      style={{ background: `${color}15`, color }}
    >
      {type}
    </span>
  );
}

export function WikiCard({ artifact }: { artifact: Artifact }) {
  const tags = parseTags(artifact.tags);
  const summary = artifact.summary ?? "";
  const excerpt = summary.length > 120 ? `${summary.slice(0, 120)}…` : summary;
  const date = artifact.created_at.slice(0, 10);

  // Infer type from first tag, or default to "research"
  const type = tags[0] ?? "research";

  return (
    <Link href={`/wiki/${artifact.slug}`} className="block h-full">
      <article className="app-card h-full group">
        <TypeBadge type={type} />
        <h3
          className="text-base font-medium mt-3 mb-2 group-hover:text-[var(--ink)] transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] line-clamp-1"
          style={{ color: "var(--ink)" }}
        >
          {artifact.title}
        </h3>
        <p className="text-sm leading-relaxed line-clamp-2" style={{ color: "var(--ink-muted)" }}>
          {excerpt}
        </p>
        <div className="flex items-center gap-2 mt-4">
          <span className="text-xs" style={{ color: "var(--ink-faint)" }}>
            {date}
          </span>
          {tags.length > 1 &&
            tags.slice(1, 3).map((tag) => (
              <span
                key={tag}
                className="text-[10px] px-1.5 py-0.5 rounded"
                style={{
                  background: "var(--surface-2)",
                  color: "var(--ink-muted)",
                }}
              >
                {tag}
              </span>
            ))}
        </div>
      </article>
    </Link>
  );
}
