import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { GET } from "@/app/api/artifacts/route";

function jsonResponse(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("GET /api/artifacts", () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    fetchSpy = vi.spyOn(globalThis, "fetch");
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns an empty array when backend returns empty", async () => {
    fetchSpy.mockResolvedValueOnce(jsonResponse([]));

    const response = await GET();
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body).toEqual([]);
  });

  it("returns all artifacts as a JSON array", async () => {
    const artifacts = [
      { id: 1, slug: "alpha", title: "Alpha" },
      { id: 2, slug: "beta", title: "Beta" },
    ];
    fetchSpy.mockResolvedValueOnce(jsonResponse(artifacts));

    const response = await GET();
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body).toHaveLength(2);
  });

  it("returns 502 when backend is unreachable", async () => {
    fetchSpy.mockRejectedValueOnce(new Error("ECONNREFUSED"));

    const response = await GET();
    expect(response.status).toBe(502);
    const body = await response.json();
    expect(body).toHaveProperty("error");
  });

  it("forwards backend error status", async () => {
    fetchSpy.mockResolvedValueOnce(new Response("Internal Server Error", { status: 500 }));

    const response = await GET();
    expect(response.status).toBe(500);
  });
});
