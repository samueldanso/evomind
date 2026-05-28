import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type Database from "better-sqlite3";
import { NextRequest } from "next/server";
import { insertArtifact, makeTestDb } from "../helpers/db";

const { mockGetDb } = vi.hoisted(() => ({
  mockGetDb: vi.fn<() => Database.Database>(),
}));

vi.mock("@/lib/db", () => ({ getDb: mockGetDb }));

import { GET } from "@/app/api/search/route";

/**
 * The search route accesses request.nextUrl.searchParams, which is a
 * Next.js extension only present on NextRequest (not plain Request).
 * Construct NextRequest directly so nextUrl is populated.
 */
function makeRequest(q: string): NextRequest {
  const url = `http://localhost/api/search?q=${encodeURIComponent(q)}`;
  return new NextRequest(url);
}

function makeRequestNoQ(): NextRequest {
  return new NextRequest("http://localhost/api/search");
}

describe("GET /api/search", () => {
  let db: Database.Database;

  beforeEach(() => {
    db = makeTestDb();
    mockGetDb.mockReturnValue(db);
  });

  afterEach(() => {
    db.close();
    vi.clearAllMocks();
  });

  // ── Empty / missing query ──────────────────────────────────────────────────

  it("returns all artifacts when q is an empty string", async () => {
    insertArtifact(db, { slug: "a", title: "Alpha" });
    insertArtifact(db, { slug: "b", title: "Beta" });

    const response = await GET(makeRequest(""));
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body).toHaveLength(2);
  });

  it("returns all artifacts when q param is absent", async () => {
    insertArtifact(db, { slug: "a", title: "Alpha" });

    const response = await GET(makeRequestNoQ());
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body).toHaveLength(1);
  });

  it("returns all artifacts in created_at DESC order when q is empty", async () => {
    insertArtifact(db, {
      slug: "old",
      title: "Old",
      created_at: "2024-01-01T00:00:00.000Z",
    });
    insertArtifact(db, {
      slug: "new",
      title: "New",
      created_at: "2024-12-01T00:00:00.000Z",
    });

    const response = await GET(makeRequest(""));
    const body = await response.json();
    expect(body[0].slug).toBe("new");
    expect(body[1].slug).toBe("old");
  });

  it("returns an empty array when there are no artifacts and q is empty", async () => {
    const response = await GET(makeRequest(""));
    const body = await response.json();
    expect(body).toEqual([]);
  });

  // ── FTS5 matching ──────────────────────────────────────────────────────────

  it("returns matching artifacts for a single-word FTS query", async () => {
    insertArtifact(db, {
      slug: "transformers",
      title: "Attention Is All You Need",
      summary: "Transformer architecture paper.",
      tags: "nlp,attention",
      topics: "deep-learning",
    });
    insertArtifact(db, {
      slug: "unrelated",
      title: "Unrelated Article",
      summary: "Nothing to do with the topic.",
      tags: "misc",
      topics: "other",
    });

    const response = await GET(makeRequest("Attention"));
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body.length).toBeGreaterThanOrEqual(1);
    expect(body.some((a: { slug: string }) => a.slug === "transformers")).toBe(true);
  });

  it("returns an empty array when no artifacts match the query", async () => {
    insertArtifact(db, { slug: "a", title: "Alpha", topics: "biology" });

    const response = await GET(makeRequest("quantumcomputing"));
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body).toEqual([]);
  });

  it("searches across tags field", async () => {
    insertArtifact(db, {
      slug: "tagged",
      title: "Tagged Article",
      tags: "reinforcement-learning,rl",
      topics: "ai",
    });

    const response = await GET(makeRequest("reinforcement-learning"));
    const body = await response.json();
    expect(body.some((a: { slug: string }) => a.slug === "tagged")).toBe(true);
  });

  it("searches across topics field", async () => {
    insertArtifact(db, {
      slug: "topic-match",
      title: "Topic Match",
      tags: "misc",
      topics: "mechanistic-interpretability",
    });

    const response = await GET(makeRequest("mechanistic-interpretability"));
    const body = await response.json();
    expect(body.some((a: { slug: string }) => a.slug === "topic-match")).toBe(true);
  });

  // ── Special character handling (ftsEscape) ─────────────────────────────────

  it("does not throw on a query containing double quotes", async () => {
    // A bare `"` passed to FTS5 MATCH would throw a syntax error without
    // ftsEscape(). This verifies the handler never lets raw quotes reach SQL.
    const response = await GET(makeRequest('"quoted query"'));
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(Array.isArray(body)).toBe(true);
  });

  it("does not throw on a query that is only double quotes", async () => {
    // All tokens become empty strings after stripping quotes — ftsEscape
    // filters them out and produces an empty escaped string, which falls
    // through to the all-artifacts path.
    const response = await GET(makeRequest('"""'));
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(Array.isArray(body)).toBe(true);
  });

  it("does not throw on a query with leading/trailing whitespace", async () => {
    const response = await GET(makeRequest("  transformer  "));
    expect(response.status).toBe(200);
  });

  it("does not throw on a query containing hyphens", async () => {
    // Hyphens are problematic in FTS5 unless tokens are quoted.
    const response = await GET(makeRequest("step-by-step"));
    expect(response.status).toBe(200);
    expect(Array.isArray(await response.json())).toBe(true);
  });

  it("does not throw on a multi-word query", async () => {
    insertArtifact(db, {
      slug: "multi",
      title: "Large Language Models",
      topics: "llm",
    });

    const response = await GET(makeRequest("large language models"));
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(Array.isArray(body)).toBe(true);
  });

  // ── Error handling ─────────────────────────────────────────────────────────

  it("returns 500 when the database throws", async () => {
    mockGetDb.mockImplementation(() => {
      throw new Error("DB unavailable");
    });

    const response = await GET(makeRequest("anything"));
    expect(response.status).toBe(500);
    const body = await response.json();
    expect(body).toHaveProperty("error");
  });
});
