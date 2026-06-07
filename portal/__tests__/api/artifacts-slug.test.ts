import type { Database } from "bun:sqlite";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { insertArtifact, makeTestDb } from "../helpers/db";

const mockGetDb = vi.fn<() => Database>();

vi.mock("@/lib/db", () => ({ getDb: mockGetDb }));

import { GET } from "@/app/api/artifacts/[slug]/route";

/** Minimal ctx shape the Next.js handler expects. */
function makeCtx(slug: string) {
  return { params: Promise.resolve({ slug }) };
}

describe("GET /api/artifacts/[slug]", () => {
  let db: Database;

  beforeEach(() => {
    db = makeTestDb();
    mockGetDb.mockReturnValue(db);
  });

  afterEach(() => {
    db.close();
    vi.clearAllMocks();
  });

  it("returns the artifact JSON for a known slug", async () => {
    insertArtifact(db, {
      slug: "my-artifact",
      title: "My Artifact",
      summary: "Summary text.",
      tags: "ml,nlp",
      topics: "ai",
    });

    const req = new Request("http://localhost/api/artifacts/my-artifact");
    const response = await GET(req as never, makeCtx("my-artifact"));

    expect(response.status).toBe(200);

    const body = await response.json();
    expect(body.slug).toBe("my-artifact");
    expect(body.title).toBe("My Artifact");
    expect(body.summary).toBe("Summary text.");
  });

  it("returns 404 for an unknown slug", async () => {
    const req = new Request("http://localhost/api/artifacts/does-not-exist");
    const response = await GET(req as never, makeCtx("does-not-exist"));

    expect(response.status).toBe(404);

    const body = await response.json();
    expect(body).toHaveProperty("error");
  });

  it("returns 404 when the table is empty", async () => {
    const req = new Request("http://localhost/api/artifacts/anything");
    const response = await GET(req as never, makeCtx("anything"));

    expect(response.status).toBe(404);
  });

  it("returns 500 when the database throws", async () => {
    mockGetDb.mockImplementation(() => {
      throw new Error("DB unavailable");
    });

    const req = new Request("http://localhost/api/artifacts/boom");
    const response = await GET(req as never, makeCtx("boom"));

    expect(response.status).toBe(500);
    const body = await response.json();
    expect(body).toHaveProperty("error");
  });

  it("does not confuse slugs that share a common prefix", async () => {
    insertArtifact(db, { slug: "transformer", title: "Transformer" });
    insertArtifact(db, { slug: "transformer-xl", title: "Transformer XL" });

    const req = new Request("http://localhost/api/artifacts/transformer");
    const response = await GET(req as never, makeCtx("transformer"));

    const body = await response.json();
    expect(body.slug).toBe("transformer");
    expect(body.title).toBe("Transformer");
  });
});
