"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { chat, type ChatResponse, type ChatSource } from "@/lib/chat";
import { Search, Loader2 } from "lucide-react";

export default function ChatPage() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await chat(trimmed);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
        <header className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Research Chat</h1>
          <p className="mt-1 text-muted-foreground">
            Ask questions grounded in your research corpus
          </p>
        </header>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="What would you like to know?"
            disabled={loading}
            className="flex-1"
          />
          <Button type="submit" disabled={loading || !query.trim()}>
            {loading ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Search className="size-4" />
            )}
          </Button>
        </form>

        {error && (
          <Card className="mt-6 border-destructive/50">
            <CardContent className="pt-4">
              <p className="text-sm text-destructive">{error}</p>
            </CardContent>
          </Card>
        )}

        {loading && (
          <div className="mt-8 flex items-center gap-2 text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            <span className="text-sm">Searching corpus and generating answer...</span>
          </div>
        )}

        {result && (
          <div className="mt-8 space-y-6">
            <section>
              <h2 className="mb-3 text-sm font-medium text-muted-foreground uppercase tracking-wide">
                Answer
              </h2>
              <div className="prose prose-neutral dark:prose-invert max-w-none rounded-lg border bg-card p-5 text-sm leading-relaxed">
                {result.answer}
              </div>
            </section>

            {result.sources.length > 0 && (
              <section>
                <h2 className="mb-3 text-sm font-medium text-muted-foreground uppercase tracking-wide">
                  Sources ({result.sources.length})
                </h2>
                <div className="space-y-3">
                  {result.sources.map((source, i) => (
                    <SourceCard key={`${source.slug}-${i}`} source={source} />
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function SourceCard({ source }: { source: ChatSource }) {
  return (
    <Card size="sm">
      <CardHeader className="flex-row items-center gap-2">
        <CardTitle className="flex-1 truncate">{source.title}</CardTitle>
        <Badge variant="secondary">{source.match_type}</Badge>
        <span className="text-xs text-muted-foreground tabular-nums">
          {source.score.toFixed(2)}
        </span>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-muted-foreground line-clamp-2">{source.excerpt}</p>
      </CardContent>
    </Card>
  );
}
