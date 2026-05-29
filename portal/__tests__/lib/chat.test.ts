import { afterEach, beforeEach, describe, expect, it, mock, spyOn } from "bun:test";
import { chat } from "@/lib/chat";

describe("chat()", () => {
  let fetchSpy: ReturnType<typeof spyOn>;

  beforeEach(() => {
    fetchSpy = spyOn(globalThis, "fetch");
  });

  afterEach(() => {
    fetchSpy.mockRestore();
  });

  it("returns a ChatResponse on successful request", async () => {
    const payload = {
      answer: "SQLite is a lightweight database.",
      sources: [
        {
          slug: "sqlite-overview",
          title: "SQLite Overview",
          excerpt: "SQLite is a C-language library...",
          score: 0.89,
          match_type: "hybrid",
        },
      ],
    };

    fetchSpy.mockResolvedValueOnce(
      new Response(JSON.stringify(payload), { status: 200 })
    );

    const result = await chat("What is SQLite?");

    expect(fetchSpy).toHaveBeenCalledWith("http://localhost:8765/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: "What is SQLite?", limit: 5 }),
    });
    expect(result.answer).toBe(payload.answer);
    expect(result.sources).toHaveLength(1);
    expect(result.sources[0].slug).toBe("sqlite-overview");
    expect(result.sources[0].score).toBe(0.89);
    expect(result.sources[0].match_type).toBe("hybrid");
  });

  it("passes custom limit to the request body", async () => {
    fetchSpy.mockResolvedValueOnce(
      new Response(JSON.stringify({ answer: "...", sources: [] }), { status: 200 })
    );

    await chat("query", 10);

    const body = JSON.parse((fetchSpy.mock.calls[0] as [string, RequestInit])[1].body as string);
    expect(body.limit).toBe(10);
  });

  it("throws an error when the response is not ok", async () => {
    fetchSpy.mockResolvedValueOnce(
      new Response(JSON.stringify({ error: "Embedding failed: timeout" }), { status: 500 })
    );

    await expect(chat("bad query")).rejects.toThrow("Embedding failed: timeout");
  });

  it("throws a generic error when error body is not parseable", async () => {
    fetchSpy.mockResolvedValueOnce(
      new Response("not json", { status: 503 })
    );

    await expect(chat("query")).rejects.toThrow(
      "Chat request failed with status 503"
    );
  });
});
