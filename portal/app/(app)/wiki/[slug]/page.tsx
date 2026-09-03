import fs from "node:fs";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Calendar, Tag, Clock } from "@phosphor-icons/react/dist/ssr";
import { ArtifactViewer } from "@/components/artifact-viewer";
import { getDb } from "@/lib/db";
import { assertInsideVault } from "@/lib/path-guard";
import type { Artifact } from "@/lib/types";
import { parseTags } from "@/lib/utils";

function readHtmlContent(artifact: Artifact): string | null {
  if (!artifact.html_path) return null;
  try {
    const safePath = assertInsideVault(artifact.html_path);
    if (!fs.existsSync(safePath)) return null;
    return fs.readFileSync(safePath, "utf-8");
  } catch {
    return null;
  }
}

function estimateReadingTime(text: string): number {
  const words = text.split(/\s+/).length;
  return Math.max(1, Math.round(words / 200));
}

export default async function WikiDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;

  let artifact: Artifact | undefined;
  try {
    const db = getDb();
    artifact = db.prepare("SELECT * FROM artifacts WHERE slug = ?").get(slug) as
      | Artifact
      | undefined;
  } catch (err) {
    console.error("[WikiDetail] DB error for slug", slug, err);
    notFound();
  }

  if (!artifact) notFound();

  const tags = parseTags(artifact.tags);
  const date = artifact.created_at.slice(0, 10);
  const htmlContent = readHtmlContent(artifact);
  const readTime = estimateReadingTime(artifact.summary ?? "");

  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-6xl px-6 py-8">
        {/* Breadcrumb */}
        <nav className="mb-8">
          <Link
            href="/wiki"
            className="inline-flex items-center gap-1.5 text-sm transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] hover:text-[#f5f5f4]"
            style={{ color: "rgba(245,245,244,0.4)" }}
          >
            <ArrowLeft size={14} weight="bold" />
            Back to wiki
          </Link>
        </nav>

        <div className="flex flex-col lg:flex-row gap-10">
          {/* Content */}
          <div className="flex-1 min-w-0">
            <header className="mb-8">
              <h1
                className="text-2xl sm:text-3xl font-semibold tracking-tight text-balance"
                style={{ color: "#f5f5f4", letterSpacing: "-0.02em" }}
              >
                {artifact.title}
              </h1>

              {artifact.summary && (
                <p
                  className="mt-4 text-lg leading-relaxed font-medium text-pretty"
                  style={{ color: "rgba(245,245,244,0.55)" }}
                >
                  {artifact.summary}
                </p>
              )}
            </header>

            {htmlContent ? (
              <ArtifactViewer html={htmlContent} />
            ) : (
              <div className="surface-card p-8">
                <div className="wiki-prose">
                  <p>{artifact.summary}</p>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <aside className="w-full lg:w-[280px] flex-shrink-0">
            <div className="lg:sticky lg:top-8 space-y-6">
              {/* Metadata card */}
              <div className="surface-card p-5 space-y-4">
                <h4
                  className="text-xs font-medium uppercase tracking-wider"
                  style={{ color: "rgba(245,245,244,0.35)" }}
                >
                  Details
                </h4>

                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Calendar size={14} weight="bold" style={{ color: "rgba(245,245,244,0.3)" }} />
                    <span className="text-sm" style={{ color: "rgba(245,245,244,0.6)" }}>
                      {date}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock size={14} weight="bold" style={{ color: "rgba(245,245,244,0.3)" }} />
                    <span className="text-sm" style={{ color: "rgba(245,245,244,0.6)" }}>
                      {readTime} min read
                    </span>
                  </div>
                </div>

                {tags.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Tag size={14} weight="bold" style={{ color: "rgba(245,245,244,0.3)" }} />
                      <span
                        className="text-xs font-medium uppercase tracking-wider"
                        style={{ color: "rgba(245,245,244,0.35)" }}
                      >
                        Tags
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {tags.map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-0.5 rounded text-xs font-medium"
                          style={{
                            background: "rgba(255,255,255,0.04)",
                            color: "rgba(245,245,244,0.5)",
                            border: "1px solid rgba(255,255,255,0.06)",
                          }}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
