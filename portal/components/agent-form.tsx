"use client";

import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { dispatchAgent } from "@/lib/agent-client";
import type { AgentResponse } from "@/lib/agent-client";
import { RunStatus } from "./run-status";

export function AgentForm() {
  const searchParams = useSearchParams();
  const [topic, setTopic] = useState("");
  const [taskType, setTaskType] = useState<"research" | "teach">("research");
  const [mode, setMode] = useState<"concept" | "tool" | "company">("concept");
  const [artifactSlug, setArtifactSlug] = useState("");
  const [context, setContext] = useState("");
  const [showContext, setShowContext] = useState(false);
  const [autoTeach, setAutoTeach] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AgentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const taskParam = searchParams.get("task");
    const slugParam = searchParams.get("slug");
    if (taskParam === "teach") setTaskType("teach");
    if (slugParam) {
      setArtifactSlug(slugParam);
      setTopic((prev) => {
        if (prev) return prev;
        return slugParam
          .replace(/-/g, " ")
          .replace(/\b\w/g, (c) => c.toUpperCase());
      });
    }
  }, [searchParams]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = topic.trim();
    if (!trimmed) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await dispatchAgent({
        task_type: taskType,
        topic: trimmed,
        ...(taskType === "research" && { mode, auto_teach: autoTeach }),
        ...(taskType === "teach" && artifactSlug && { artifact_slug: artifactSlug }),
        ...(context.trim() && { context: context.trim() }),
      });
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="topic" className="block text-sm font-medium mb-1">
            Topic
          </label>
          <input
            id="topic"
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g. KV Cache, vLLM, attention mechanism"
            disabled={loading}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Task</label>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setTaskType("research")}
              disabled={loading}
              className={`rounded-md border px-4 py-1.5 text-sm font-medium transition-colors ${
                taskType === "research"
                  ? "bg-foreground text-background"
                  : "hover:bg-accent"
              }`}
            >
              Research
            </button>
            <button
              type="button"
              onClick={() => setTaskType("teach")}
              disabled={loading}
              className={`rounded-md border px-4 py-1.5 text-sm font-medium transition-colors ${
                taskType === "teach"
                  ? "bg-foreground text-background"
                  : "hover:bg-accent"
              }`}
            >
              Teaching
            </button>
          </div>
        </div>

        {taskType === "research" && (
          <div>
            <label htmlFor="mode" className="block text-sm font-medium mb-1">
              Mode
            </label>
            <select
              id="mode"
              value={mode}
              onChange={(e) => setMode(e.target.value as "concept" | "tool" | "company")}
              disabled={loading}
              className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="concept">Concept</option>
              <option value="tool">Tool</option>
              <option value="company">Company</option>
            </select>
          </div>
        )}

        {taskType === "teach" && (
          <div>
            <label htmlFor="slug" className="block text-sm font-medium mb-1">
              Artifact slug (optional)
            </label>
            <input
              id="slug"
              type="text"
              value={artifactSlug}
              onChange={(e) => setArtifactSlug(e.target.value)}
              placeholder="e.g. kv-cache"
              disabled={loading}
              className="w-full rounded-md border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
        )}

        {!showContext ? (
          <button
            type="button"
            onClick={() => setShowContext(true)}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            + Add context
          </button>
        ) : (
          <div>
            <label htmlFor="context" className="block text-sm font-medium mb-1">
              Additional context
            </label>
            <textarea
              id="context"
              value={context}
              onChange={(e) => setContext(e.target.value)}
              rows={3}
              disabled={loading}
              className="w-full rounded-md border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
        )}

        {taskType === "research" && (
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={autoTeach}
              onChange={(e) => setAutoTeach(e.target.checked)}
              disabled={loading}
              className="rounded border"
            />
            Auto-teach after research
          </label>
        )}

        <button
          type="submit"
          disabled={loading || !topic.trim()}
          className="inline-flex items-center gap-2 rounded-md bg-foreground px-4 py-2 text-sm font-medium text-background transition-colors hover:bg-foreground/90 disabled:opacity-50"
        >
          {loading && <Loader2 className="size-4 animate-spin" />}
          {loading ? "Running agent..." : "Run"}
        </button>
      </form>

      {error && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-4">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {result && <RunStatus response={result} />}
    </div>
  );
}
