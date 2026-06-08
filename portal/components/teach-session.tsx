"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { getAgentRun, sendMessage } from "@/lib/agent-client";

type Message = { role: string; content: string };

export function TeachSession({
  runId,
  topic,
  initialReply,
}: {
  runId: number;
  topic?: string;
  initialReply?: string;
}) {
  const [messages, setMessages] = useState<Message[]>(() =>
    initialReply ? [{ role: "assistant", content: initialReply }] : [],
  );
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<string>("paused_awaiting_input");
  const [error, setError] = useState<string | null>(null);
  const [checklistSlug, setChecklistSlug] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    if (status !== "running") {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    intervalRef.current = setInterval(async () => {
      try {
        const { run } = await getAgentRun(runId);
        setStatus(run.status);
        if (run.session_log && run.session_log.length > messages.length) {
          setMessages(run.session_log);
        }
        if (run.status === "complete" && run.output) {
          const slug = (run.output as Record<string, unknown>).checklist_slug;
          if (slug) setChecklistSlug(String(slug));
        }
      } catch {
        // polling failure is non-fatal
      }
    }, 2000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [status, runId, messages.length]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const content = input.trim();
    if (!content || status !== "paused_awaiting_input") return;

    setMessages((prev) => [...prev, { role: "user", content }]);
    setInput("");
    setStatus("running");

    try {
      const res = await sendMessage(runId, content);
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply }]);
      if (res.status === "complete") {
        setStatus("complete");
      } else {
        setStatus("paused_awaiting_input");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message");
      setStatus("paused_awaiting_input");
    }
  };

  const isInputEnabled = status === "paused_awaiting_input";
  const isComplete = status === "complete";

  return (
    <div className="flex flex-col gap-4">
      {topic && (
        <h2 className="text-lg font-semibold">
          {topic}
        </h2>
      )}

      <div className="space-y-4">
        {messages.map((msg, i) => (
          <div
            key={`${msg.role}-${i}`}
            className={`rounded-lg p-4 text-sm leading-relaxed whitespace-pre-wrap ${
              msg.role === "assistant"
                ? "bg-muted"
                : "bg-primary/5 border ml-6"
            }`}
          >
            {msg.content}
          </div>
        ))}

        {status === "running" && (
          <div className="bg-muted rounded-lg p-4 text-sm text-muted-foreground">
            <span className="inline-flex items-center gap-1.5">
              <span className="size-1.5 rounded-full bg-current animate-pulse" />
              <span className="size-1.5 rounded-full bg-current animate-pulse [animation-delay:150ms]" />
              <span className="size-1.5 rounded-full bg-current animate-pulse [animation-delay:300ms]" />
            </span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {isComplete && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-900/20">
          <p className="text-sm font-medium text-green-800 dark:text-green-300">
            Session complete
          </p>
          {checklistSlug && (
            <Link
              href={`/artifacts/${checklistSlug}`}
              className="mt-1 inline-block text-sm text-green-700 underline hover:text-green-900 dark:text-green-400 dark:hover:text-green-200"
            >
              View mastery checklist
            </Link>
          )}
        </div>
      )}

      {!isComplete && (
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={!isInputEnabled}
            placeholder={isInputEnabled ? "Type your response..." : ""}
            className="flex-1 rounded-lg border bg-background px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
            autoFocus
          />
          <button
            type="submit"
            disabled={!isInputEnabled || !input.trim()}
            className="rounded-lg bg-foreground px-5 py-2.5 text-sm font-medium text-background disabled:opacity-50"
          >
            Send
          </button>
        </form>
      )}
    </div>
  );
}
