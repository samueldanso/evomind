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
  } catch {
    return Response.json([]);
  }
}
