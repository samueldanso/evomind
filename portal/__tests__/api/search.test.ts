import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { GET } from "@/app/api/search/route";

function jsonResponse(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function makeRequest(q: string): NextRequest {
  const url = `http://localhost/api/search?q=${encodeURIComponent(q)}`;
  return new NextRequest(url);
}

function makeRequestNoQ(): NextRequest {
  return new NextRequest("http://localhost/api/search");
}

describe("GET /api/search", () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    fetchSpy = vi.spyOn(globalThis, "fetch");
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("proxies empty query to backend", async () => {
    fetchSpy.mockResolvedValueOnce(jsonResponse([]));

    const response = await GET(makeRequest(""));
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body).toEqual([]);
  });

  it("proxies absent q param to backend", async () => {
    const artifacts = [{ id: 1, slug: "a", title: "Alpha" }];
    fetchSpy.mockResolvedValueOnce(jsonResponse(artifacts));

    const response = await GET(makeRequestNoQ());
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body).toHaveLength(1);
  });

  it("proxies search query to backend", async () => {
    const results = [{ id: 1, slug: "transformers", title: "Attention" }];
    fetchSpy.mockResolvedValueOnce(jsonResponse(results));

    const response = await GET(makeRequest("Attention"));
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body).toHaveLength(1);
    expect(body[0].slug).toBe("transformers");
  });

  it("passes query string through to backend URL", async () => {
    fetchSpy.mockResolvedValueOnce(jsonResponse([]));

    await GET(makeRequest("large language models"));

    expect(fetchSpy).toHaveBeenCalledOnce();
    const calledUrl = fetchSpy.mock.calls[0][0];
    expect(calledUrl).toContain("q=large%20language%20models");
  });

  it("returns 502 when backend is unreachable", async () => {
    fetchSpy.mockRejectedValueOnce(new Error("ECONNREFUSED"));

    const response = await GET(makeRequest("anything"));
    expect(response.status).toBe(502);
    const body = await response.json();
    expect(body).toHaveProperty("error");
  });

  it("forwards backend error status", async () => {
    fetchSpy.mockResolvedValueOnce(new Response("Server Error", { status: 500 }));

    const response = await GET(makeRequest("anything"));
    expect(response.status).toBe(500);
  });
});
