import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { chat } from "@/lib/chat";

describe("chat()", () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    fetchSpy = vi.spyOn(globalThis, "fetch");
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns parsed response on success", async () => {
    const mockResponse = {
      answer: "Test answer",
      sources: [
        {
          slug: "test-slug",
          title: "Test Title",
          excerpt: "Test excerpt",
          score: 0.9,
          match_type: "vec",
        },
      ],
    };

    fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(mockResponse), { status: 200 }));

    const result = await chat("test query");
    expect(result.answer).toBe("Test answer");
    expect(result.sources).toHaveLength(1);
    expect(result.sources[0].slug).toBe("test-slug");
  });

  it("throws on non-200 response", async () => {
    fetchSpy.mockResolvedValueOnce(
      new Response(JSON.stringify({ error: "Bad request" }), { status: 400 })
    );

    await expect(chat("bad query")).rejects.toThrow();
  });

  it("posts to correct endpoint with query", async () => {
    fetchSpy.mockResolvedValueOnce(
      new Response(JSON.stringify({ answer: "ok", sources: [] }), {
        status: 200,
      })
    );

    await chat("my question");

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining("/chat"),
      expect.objectContaining({
        method: "POST",
        body: expect.stringContaining("my question"),
      })
    );
  });

  it("throws on network error", async () => {
    fetchSpy.mockRejectedValueOnce(new Error("Network error"));
    await expect(chat("fail")).rejects.toThrow("Network error");
  });
});
