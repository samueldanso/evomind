"use client";

import Link from "next/link";
import type { AgentResponse, AgentRunData } from "@/lib/agent-client";

function RunCard({ run, label }: { run: AgentRunData; label: string }) {
  const slug = (
    run.output && typeof run.output === "object"
      ? (run.output as Record<string, unknown>).artifact_slug ||
        (run.output as Record<string, unknown>).checklist_slug
      : null
  ) as string | null;

  return (
    <div className="rounded-lg border p-4 space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium">{label}</span>
        <span
          className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
            run.status === "complete"
              ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
              : run.status === "failed"
                ? "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
                : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400"
          }`}
        >
          {run.status}
        </span>
        <span className="text-xs text-muted-foreground ml-auto">
          {run.cost_tokens} tokens
        </span>
      </div>

      {run.status === "failed" && run.error && (
        <p className="text-xs text-destructive">{run.error}</p>
      )}

      {run.status === "complete" && slug && (
        <Link
          href={`/artifacts/${slug}`}
          className="inline-block text-xs text-blue-600 hover:underline dark:text-blue-400"
        >
          View artifact: {String(slug)}
        </Link>
      )}
    </div>
  );
}

export function RunStatus({ response }: { response: AgentResponse }) {
  return (
    <div className="space-y-3">
      <RunCard run={response.run} label="Research" />
      {response.teach_run && response.teach_run.status !== "paused_awaiting_input" && (
        <RunCard run={response.teach_run} label="Teaching" />
      )}
    </div>
  );
}
