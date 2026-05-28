import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { Artifact } from "@/lib/types";
import { parseTags } from "@/lib/utils";

function formatDate(iso: string): string {
  return iso.slice(0, 10);
}

export function ArtifactCard({ artifact }: { artifact: Artifact }) {
  const tags = parseTags(artifact.tags);
  const summary = artifact.summary ?? "";
  const excerpt = summary.length > 150 ? `${summary.slice(0, 150)}…` : summary;

  return (
    <Link href={`/artifacts/${artifact.slug}`} className="block h-full">
      <Card className="h-full transition-shadow hover:shadow-md">
        <CardHeader>
          <CardTitle>{artifact.title}</CardTitle>
          <CardDescription>{formatDate(artifact.created_at)}</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <p className="text-sm text-muted-foreground leading-relaxed">{excerpt}</p>
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {tags.map((tag) => (
                <Badge key={tag} variant="secondary">
                  {tag}
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
