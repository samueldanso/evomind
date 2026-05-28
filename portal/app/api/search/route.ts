import { getDb } from "@/lib/db";
import type { Artifact } from "@/lib/types";
import type { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

function ftsEscape(query: string): string {
  // Wrap each token in double quotes so FTS5 treats hyphens and special chars
  // as literals — mirrors the same escaping in scripts/ingest.py
  return query
    .trim()
    .split(/\s+/)
    .map((t) => `"${t}"`)
    .join(" ");
}

export function GET(request: NextRequest) {
  const q = request.nextUrl.searchParams.get("q")?.trim() ?? "";

  try {
    const db = getDb();

    if (!q) {
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
      .all(ftsEscape(q)) as Artifact[];

    return Response.json(artifacts);
  } catch (err) {
    console.error("[GET /api/search]", err);
    return Response.json({ error: "Search failed" }, { status: 500 });
  }
}
