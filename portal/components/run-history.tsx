"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listRuns } from "@/lib/agent-client";
import type { RunHistoryItem } from "@/lib/agent-client";

export function RunHistory() {
  const [runs, setRuns] = useState<RunHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listRuns(20)
      .then((data) => setRuns(data.runs))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load runs"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <p className="text-sm text-muted-foreground">Loading runs...</p>;
  }

  if (error) {
    return <p className="text-sm text-destructive">{error}</p>;
  }

  if (runs.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No runs yet. Start by running an agent above.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {runs.map((run) => {
        const topic =
          run.task_input && typeof run.task_input === "object"
            ? (run.task_input as Record<string, unknown>).topic
            : null;
        const slug = (
          run.output && typeof run.output === "object"
            ? (run.output as Record<string, unknown>).artifact_slug ||
              (run.output as Record<string, unknown>).checklist_slug
            : null
        ) as string | null;
        const date = run.started_at ? run.started_at.slice(0, 10) : "";

        return (
          <div key={run.id} className="flex items-center gap-3 rounded-lg border p-3">
            <span
              className={`inline-block rounded px-1.5 py-0.5 text-xs font-medium ${
                run.agent_type === "research_agent"
                  ? "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400"
                  : "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400"
              }`}
            >
              {run.agent_type === "research_agent" ? "Research" : "Teaching"}
            </span>
            <span
              className={`inline-block rounded-full px-1.5 py-0.5 text-xs ${
                run.status === "complete"
                  ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
                  : run.status === "failed"
                    ? "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
                    : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400"
              }`}
            >
              {run.status}
            </span>
            <span className="flex-1 truncate text-sm">
              {topic ? String(topic) : "—"}
            </span>
            <span className="text-xs text-muted-foreground tabular-nums">
              {run.cost_tokens}t
            </span>
            <span className="text-xs text-muted-foreground">{date}</span>
            {slug && (
              <Link
                href={`/artifacts/${slug}`}
                className="text-xs text-blue-600 hover:underline dark:text-blue-400"
              >
                View
              </Link>
            )}
          </div>
        );
      })}
    </div>
  );
}
