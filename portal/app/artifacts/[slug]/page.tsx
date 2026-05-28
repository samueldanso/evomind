import { Badge } from "@/components/ui/badge";
import { getDb } from "@/lib/db";
import type { Artifact } from "@/lib/types";
import { parseTags } from "@/lib/utils";
import Link from "next/link";
import { notFound } from "next/navigation";

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

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <nav className="mb-6">
          <Link
            href="/"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            ← Research
          </Link>
        </nav>

        <header className="mb-6">
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

        <iframe
          src={`/api/artifacts/${slug}/html`}
          sandbox="allow-same-origin allow-popups"
          className="h-[80vh] w-full rounded-lg border"
          title={artifact.title}
        />
      </div>
    </div>
  );
}
