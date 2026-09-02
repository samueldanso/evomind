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
  const color = TYPE_COLORS[type.toLowerCase()] ?? "rgba(245,245,244,0.4)";
  return (
    <span
      className="inline-block px-2 py-0.5 rounded-full text-[10px] font-medium uppercase tracking-wider"
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
          className="text-base font-medium mt-3 mb-2 group-hover:text-[#f5f5f4] transition-colors duration-150 line-clamp-1"
          style={{ color: "rgba(245,245,244,0.9)" }}
        >
          {artifact.title}
        </h3>
        <p
          className="text-sm leading-relaxed line-clamp-2"
          style={{ color: "rgba(245,245,244,0.4)" }}
        >
          {excerpt}
        </p>
        <div className="flex items-center gap-2 mt-4">
          <span className="text-xs" style={{ color: "rgba(245,245,244,0.25)" }}>
            {date}
          </span>
          {tags.length > 1 &&
            tags.slice(1, 3).map((tag) => (
              <span
                key={tag}
                className="text-[10px] px-1.5 py-0.5 rounded"
                style={{
                  background: "rgba(255,255,255,0.04)",
                  color: "rgba(245,245,244,0.35)",
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
