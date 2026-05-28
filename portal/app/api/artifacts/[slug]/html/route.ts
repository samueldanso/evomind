import { getDb } from "@/lib/db";
import type { Artifact } from "@/lib/types";
import fs from "node:fs";
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
      return new Response("Not found", { status: 404 });
    }

    if (!artifact.html_path) {
      return new Response(artifact.summary ?? "No content available.", {
        status: 200,
        headers: { "Content-Type": "text/plain; charset=utf-8" },
      });
    }

    if (!fs.existsSync(artifact.html_path)) {
      return new Response("HTML file not found on disk", { status: 404 });
    }

    const html = fs.readFileSync(artifact.html_path, "utf-8");
    return new Response(html, {
      status: 200,
      headers: { "Content-Type": "text/html; charset=utf-8" },
    });
  } catch (err) {
    console.error("[GET /api/artifacts/[slug]/html]", err);
    return new Response("Internal server error", { status: 500 });
  }
}
