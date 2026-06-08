"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getAgentRun, sendMessage } from "@/lib/agent-client";

type Message = { role: string; content: string };

export function TeachSession({
  runId,
  initialReply,
}: {
  runId: number;
  initialReply?: string;
}) {
  const [messages, setMessages] = useState<Message[]>(() =>
    initialReply ? [{ role: "assistant", content: initialReply }] : [],
  );
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<string>("paused_awaiting_input");
  const [error, setError] = useState<string | null>(null);
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
    <div className="flex flex-col gap-3 rounded-lg border p-4">
      <div className="flex items-center gap-2 text-sm font-medium">
        <span>Teaching Session</span>
        <span
          className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
            isComplete
              ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
              : status === "running"
                ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400"
                : "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400"
          }`}
        >
          {isComplete ? "complete" : status === "running" ? "thinking..." : "your turn"}
        </span>
      </div>

      <div className="max-h-96 overflow-y-auto space-y-3">
        {messages.map((msg, i) => (
          <div
            key={`${msg.role}-${i}`}
            className={`rounded-md p-3 text-sm whitespace-pre-wrap ${
              msg.role === "assistant"
                ? "bg-muted"
                : "bg-primary/10 ml-8"
            }`}
          >
            {msg.content}
          </div>
        ))}
        {status === "running" && (
          <div className="bg-muted rounded-md p-3 text-sm text-muted-foreground animate-pulse">
            Thinking...
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {error && <p className="text-xs text-destructive">{error}</p>}

      {!isComplete && (
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={!isInputEnabled}
            placeholder={isInputEnabled ? "Type your response..." : "Waiting..."}
            className="flex-1 rounded-md border bg-background px-3 py-2 text-sm disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!isInputEnabled || !input.trim()}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
          >
            Send
          </button>
        </form>
      )}
    </div>
  );
}
