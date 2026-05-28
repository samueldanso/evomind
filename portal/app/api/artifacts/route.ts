import { getDb } from "@/lib/db";
import type { Artifact } from "@/lib/types";

export const dynamic = "force-dynamic";

export function GET() {
  try {
    const db = getDb();
    const artifacts = db
      .prepare("SELECT * FROM artifacts ORDER BY created_at DESC")
      .all() as Artifact[];
    return Response.json(artifacts);
  } catch (err) {
    console.error("[GET /api/artifacts]", err);
    return Response.json({ error: "Failed to load artifacts" }, { status: 500 });
  }
}
