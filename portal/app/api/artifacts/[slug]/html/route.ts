import { getDb } from "@/lib/db";
import type { Artifact } from "@/lib/types";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import type { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

function getVaultRoot(): string {
  return (
    process.env.EVO_RESEARCH_STORE ??
    path.join(
      os.homedir(),
      "Library",
      "Mobile Documents",
      "iCloud~md~obsidian",
      "Documents",
      "Samuel's Vault",
      "HomeOS",
      "Knowledge",
      "Research",
    )
  );
}

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
      console.warn("[html route] no html_path for slug:", slug, "— serving summary fallback");
      return new Response(artifact.summary ?? "No content available.", {
        status: 200,
        headers: { "Content-Type": "text/plain; charset=utf-8" },
      });
    }

    // Confine file access to the vault directory to prevent path traversal
    const resolvedPath = path.resolve(artifact.html_path);
    const vaultRoot = path.resolve(getVaultRoot());
    if (!resolvedPath.startsWith(vaultRoot + path.sep)) {
      console.error("[html route] html_path outside vault root:", resolvedPath);
      return new Response("Forbidden", { status: 403 });
    }

    if (!fs.existsSync(resolvedPath)) {
      return new Response("HTML file not found on disk", { status: 404 });
    }

    const html = fs.readFileSync(resolvedPath, "utf-8");
    return new Response(html, {
      status: 200,
      headers: {
        "Content-Type": "text/html; charset=utf-8",
        // Prevent scripts in served HTML from running — defense-in-depth
        // alongside the iframe sandbox attribute on the viewer page.
        "Content-Security-Policy": "default-src 'self' 'unsafe-inline'; script-src 'none';",
        "X-Content-Type-Options": "nosniff",
      },
    });
  } catch (err) {
    console.error("[GET /api/artifacts/[slug]/html]", err);
    return new Response("Internal server error", { status: 500 });
  }
}
