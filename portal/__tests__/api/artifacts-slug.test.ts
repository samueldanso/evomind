import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DELETE, GET } from "@/app/api/artifacts/[slug]/route";

function jsonResponse(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function makeCtx(slug: string) {
  return { params: Promise.resolve({ slug }) };
}

describe("GET /api/artifacts/[slug]", () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    fetchSpy = vi.spyOn(globalThis, "fetch");
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns the artifact JSON for a known slug", async () => {
    const artifact = { id: 1, slug: "my-artifact", title: "My Artifact" };
    fetchSpy.mockResolvedValueOnce(jsonResponse(artifact));

    const req = new Request("http://localhost/api/artifacts/my-artifact");
    const response = await GET(req as never, makeCtx("my-artifact"));

    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body.slug).toBe("my-artifact");
  });

  it("returns 404 for an unknown slug", async () => {
    fetchSpy.mockResolvedValueOnce(
      new Response(JSON.stringify({ error: "Not found" }), { status: 404 })
    );

    const req = new Request("http://localhost/api/artifacts/nonexistent");
    const response = await GET(req as never, makeCtx("nonexistent"));

    expect(response.status).toBe(404);
  });

  it("returns 502 when backend is unreachable", async () => {
    fetchSpy.mockRejectedValueOnce(new Error("ECONNREFUSED"));

    const req = new Request("http://localhost/api/artifacts/any");
    const response = await GET(req as never, makeCtx("any"));

    expect(response.status).toBe(502);
  });
});

describe("DELETE /api/artifacts/[slug]", () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    fetchSpy = vi.spyOn(globalThis, "fetch");
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns 204 on successful delete", async () => {
    fetchSpy.mockResolvedValueOnce(new Response(null, { status: 204 }));

    const req = new Request("http://localhost/api/artifacts/target", {
      method: "DELETE",
    });
    const response = await DELETE(req as never, makeCtx("target"));

    expect(response.status).toBe(204);
  });

  it("returns 404 when artifact does not exist", async () => {
    fetchSpy.mockResolvedValueOnce(
      new Response(JSON.stringify({ error: "Not found" }), { status: 404 })
    );

    const req = new Request("http://localhost/api/artifacts/missing", {
      method: "DELETE",
    });
    const response = await DELETE(req as never, makeCtx("missing"));

    expect(response.status).toBe(404);
  });

  it("returns 502 when backend is unreachable", async () => {
    fetchSpy.mockRejectedValueOnce(new Error("ECONNREFUSED"));

    const req = new Request("http://localhost/api/artifacts/any", {
      method: "DELETE",
    });
    const response = await DELETE(req as never, makeCtx("any"));

    expect(response.status).toBe(502);
  });
});
