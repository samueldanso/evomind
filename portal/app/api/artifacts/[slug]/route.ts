import { getDb } from "@/lib/db";
import type { Artifact } from "@/lib/types";
import type { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

export async function GET(
  _req: NextRequest,
  ctx: { params: Promise<{ slug: string }> },
) {
  const { slug } = await ctx.params;

  try {
    const db = getDb();
    const artifact = db
      .prepare("SELECT * FROM artifacts WHERE slug = ?")
      .get(slug) as Artifact | undefined;

    if (!artifact) {
      return Response.json({ error: "Not found" }, { status: 404 });
    }

    return Response.json(artifact);
  } catch (err) {
    console.error("[GET /api/artifacts/[slug]]", err);
    return Response.json({ error: "Failed to load artifact" }, { status: 500 });
  }
}
