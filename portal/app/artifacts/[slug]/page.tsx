import { Badge } from "@/components/ui/badge";
import { getDb } from "@/lib/db";
import type { Artifact } from "@/lib/types";
import { parseTags } from "@/lib/utils";
import fs from "node:fs";
import Link from "next/link";
import { notFound } from "next/navigation";

function readHtmlContent(artifact: Artifact): string | null {
  if (!artifact.html_path) return null;
  try {
    if (!fs.existsSync(artifact.html_path)) return null;
    const raw = fs.readFileSync(artifact.html_path, "utf-8");
    // Strip outer <html>/<head>/<body> wrapper if present, keep inner content
    const bodyMatch = raw.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
    if (bodyMatch) return bodyMatch[1];
    // No body tag — strip html/head wrappers if present and return remainder
    return raw
      .replace(/<html[^>]*>/gi, "")
      .replace(/<\/html>/gi, "")
      .replace(/<head[^>]*>[\s\S]*?<\/head>/gi, "")
      .trim();
  } catch {
    return null;
  }
}

export default async function ArtifactPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  let artifact: Artifact | undefined;
  try {
    const db = getDb();
    artifact = db
      .prepare("SELECT * FROM artifacts WHERE slug = ?")
      .get(slug) as Artifact | undefined;
  } catch (err) {
    console.error("[ArtifactPage] DB error for slug", slug, err);
    notFound();
  }

  if (!artifact) {
    notFound();
  }

  const tags = parseTags(artifact.tags);
  const date = artifact.created_at.slice(0, 10);
  const htmlContent = readHtmlContent(artifact);

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        <nav className="mb-6">
          <Link
            href="/"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            ← Research
          </Link>
        </nav>

        <header className="mb-8">
          <h1 className="text-2xl font-bold tracking-tight">{artifact.title}</h1>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <span className="text-sm text-muted-foreground">{date}</span>
            {tags.map((tag) => (
              <Badge key={tag} variant="secondary">
                {tag}
              </Badge>
            ))}
          </div>
        </header>

        {htmlContent ? (
          <div
            className="prose prose-sm max-w-none rounded-lg border bg-card p-6 text-card-foreground"
            // eslint-disable-next-line react/no-danger
            dangerouslySetInnerHTML={{ __html: htmlContent }}
          />
        ) : (
          <div className="rounded-lg border bg-card p-6">
            <p className="text-sm leading-relaxed text-muted-foreground">
              {artifact.summary}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
