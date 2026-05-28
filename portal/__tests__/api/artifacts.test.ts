import type Database from "better-sqlite3";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { insertArtifact, makeTestDb } from "../helpers/db";

// vi.hoisted() runs before vi.mock() factories, so mockGetDb is defined by the
// time the factory callback executes (vi.mock is hoisted to top-of-file by
// Vitest's transform — plain `const` declarations are not).
const { mockGetDb } = vi.hoisted(() => ({
  mockGetDb: vi.fn<() => Database.Database>(),
}));

vi.mock("@/lib/db", () => ({ getDb: mockGetDb }));

import { GET } from "@/app/api/artifacts/route";

describe("GET /api/artifacts", () => {
  let db: Database.Database;

  beforeEach(() => {
    db = makeTestDb();
    mockGetDb.mockReturnValue(db);
  });

  afterEach(() => {
    db.close();
    vi.clearAllMocks();
  });

  it("returns an empty array when there are no artifacts", async () => {
    const response = await GET();
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body).toEqual([]);
  });

  it("returns all artifacts as a JSON array", async () => {
    insertArtifact(db, { slug: "alpha", title: "Alpha" });
    insertArtifact(db, { slug: "beta", title: "Beta" });

    const response = await GET();
    expect(response.status).toBe(200);

    const body = await response.json();
    expect(body).toHaveLength(2);
  });

  it("returns artifacts ordered by created_at DESC (newest first)", async () => {
    insertArtifact(db, {
      slug: "older",
      title: "Older",
      created_at: "2024-01-01T00:00:00.000Z",
    });
    insertArtifact(db, {
      slug: "newer",
      title: "Newer",
      created_at: "2024-06-01T00:00:00.000Z",
    });

    const response = await GET();
    const body = await response.json();

    expect(body[0].slug).toBe("newer");
    expect(body[1].slug).toBe("older");
  });

  it("each artifact object includes the expected fields", async () => {
    insertArtifact(db, {
      slug: "complete",
      title: "Complete Artifact",
      summary: "A complete artifact.",
      tags: "ai,llm",
      topics: "research",
    });

    const response = await GET();
    const [artifact] = await response.json();

    expect(artifact).toMatchObject({
      slug: "complete",
      title: "Complete Artifact",
      summary: "A complete artifact.",
      tags: "ai,llm",
      topics: "research",
    });
    expect(typeof artifact.id).toBe("number");
    expect(typeof artifact.created_at).toBe("string");
  });

  it("returns 500 when the database throws", async () => {
    mockGetDb.mockImplementation(() => {
      throw new Error("DB unavailable");
    });

    const response = await GET();
    expect(response.status).toBe(500);

    const body = await response.json();
    expect(body).toHaveProperty("error");
  });
});
