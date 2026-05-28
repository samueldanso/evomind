import { getDb } from "@/lib/db";
import type { Artifact } from "@/lib/types";
import type { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

function ftsEscape(query: string): string {
  // Wrap each token in double quotes so FTS5 treats hyphens and special chars
  // as literals. Strip embedded double-quotes first — FTS5 phrase literals
  // have no escape sequence for " and will throw a syntax error otherwise.
  return query
    .trim()
    .split(/\s+/)
    .map((t) => `"${t.replace(/"/g, "")}"`)
    .filter((t) => t.length > 2) // drop tokens that were pure quotes → ""
    .join(" ");
}

export function GET(request: NextRequest) {
  const q = request.nextUrl.searchParams.get("q")?.trim() ?? "";

  try {
    const db = getDb();

    const escaped = q ? ftsEscape(q) : "";

    if (!escaped) {
      const artifacts = db
        .prepare("SELECT * FROM artifacts ORDER BY created_at DESC")
        .all() as Artifact[];
      return Response.json(artifacts);
    }

    const artifacts = db
      .prepare(
        `SELECT a.*
         FROM artifacts a
         JOIN artifacts_fts f ON a.id = f.rowid
         WHERE artifacts_fts MATCH ?
         ORDER BY rank`,
      )
      .all(escaped) as Artifact[];

    return Response.json(artifacts);
  } catch (err) {
    console.error("[GET /api/search]", err);
    return Response.json({ error: "Search failed" }, { status: 500 });
  }
}
