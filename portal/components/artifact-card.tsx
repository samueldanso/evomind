import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { Artifact } from "@/lib/types";
import Link from "next/link";

function formatDate(iso: string): string {
  return iso.slice(0, 10);
}

function parseTags(tags: string): string[] {
  return tags
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean);
}

export function ArtifactCard({ artifact }: { artifact: Artifact }) {
  const tags = parseTags(artifact.tags);
  const excerpt =
    artifact.summary.length > 150
      ? `${artifact.summary.slice(0, 150)}…`
      : artifact.summary;

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
