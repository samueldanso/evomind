import path from "node:path";
import type { Database } from "bun:sqlite";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { insertArtifact, makeTestDb } from "../helpers/db";

const mockGetDb = vi.fn<() => Database>();
const mockExistsSync = vi.fn<(p: unknown) => boolean>();
const mockReadFileSync = vi.fn<(p: unknown, enc: unknown) => string>();

vi.mock("@/lib/db", () => ({ getDb: mockGetDb }));

vi.mock("node:fs", () => ({
  default: {
    existsSync: mockExistsSync,
    readFileSync: mockReadFileSync,
  },
  existsSync: mockExistsSync,
  readFileSync: mockReadFileSync,
}));

import { GET } from "@/app/api/artifacts/[slug]/html/route";

// Use a deterministic test vault root so html_path values pass the
// path-confinement check inside the route handler.
const TEST_VAULT = "/tmp/test-vault";

function htmlPath(filename: string): string {
  return path.join(TEST_VAULT, "html", filename);
}

function makeCtx(slug: string) {
  return { params: Promise.resolve({ slug }) };
}

describe("GET /api/artifacts/[slug]/html", () => {
  let db: Database;

  beforeEach(() => {
    db = makeTestDb();
    mockGetDb.mockReturnValue(db);
    // Point the route handler at our test vault root.
    process.env.EVO_STORE = TEST_VAULT;
    // Safe defaults — tests override as needed.
    mockExistsSync.mockReturnValue(false);
    mockReadFileSync.mockReturnValue("");
  });

  afterEach(() => {
    db.close();
    delete process.env.EVO_STORE;
    vi.clearAllMocks();
  });

  // ── 404 cases ─────────────────────────────────────────────────────────────

  it("returns 404 when the slug is not in the database", async () => {
    const req = new Request("http://localhost/api/artifacts/ghost/html");
    const response = await GET(req as never, makeCtx("ghost"));

    expect(response.status).toBe(404);
  });

  it("returns 404 when html_path is set but the file does not exist on disk", async () => {
    insertArtifact(db, {
      slug: "missing-file",
      title: "Missing File",
      html_path: htmlPath("missing-file.html"),
    });
    mockExistsSync.mockReturnValue(false);

    const req = new Request("http://localhost/api/artifacts/missing-file/html");
    const response = await GET(req as never, makeCtx("missing-file"));

    expect(response.status).toBe(404);
  });

  // ── Path confinement ───────────────────────────────────────────────────────

  it("returns 403 when html_path points outside the vault root", async () => {
    insertArtifact(db, {
      slug: "traversal",
      title: "Traversal",
      html_path: "/etc/passwd",
    });

    const req = new Request("http://localhost/api/artifacts/traversal/html");
    const response = await GET(req as never, makeCtx("traversal"));

    expect(response.status).toBe(403);
  });

  // ── Summary fallback ───────────────────────────────────────────────────────

  it("returns summary as text/plain when html_path is null", async () => {
    insertArtifact(db, {
      slug: "no-html",
      title: "No HTML",
      summary: "This artifact has no HTML file.",
      html_path: undefined, // stored as null
    });

    const req = new Request("http://localhost/api/artifacts/no-html/html");
    const response = await GET(req as never, makeCtx("no-html"));

    expect(response.status).toBe(200);
    expect(response.headers.get("Content-Type")).toMatch(/text\/plain/);
    const text = await response.text();
    expect(text).toBe("This artifact has no HTML file.");
  });

  it("returns fallback message as text/plain when html_path and summary are both absent", async () => {
    db.prepare(
      `INSERT INTO artifacts (slug, title, summary, tags, topics, html_path, created_at, updated_at)
       VALUES ('bare', 'Bare', null, '', '', null, datetime('now'), datetime('now'))`
    ).run();

    const req = new Request("http://localhost/api/artifacts/bare/html");
    const response = await GET(req as never, makeCtx("bare"));

    expect(response.status).toBe(200);
    expect(response.headers.get("Content-Type")).toMatch(/text\/plain/);
    const text = await response.text();
    expect(text).toBeTruthy(); // fallback string, not empty
  });

  // ── Happy path (HTML served from disk) ─────────────────────────────────────

  it("serves HTML content with text/html content-type when file exists", async () => {
    insertArtifact(db, {
      slug: "good-article",
      title: "Good Article",
      html_path: htmlPath("good-article.html"),
    });
    mockExistsSync.mockReturnValue(true);
    mockReadFileSync.mockReturnValue("<html><body>Hello</body></html>");

    const req = new Request("http://localhost/api/artifacts/good-article/html");
    const response = await GET(req as never, makeCtx("good-article"));

    expect(response.status).toBe(200);
    expect(response.headers.get("Content-Type")).toMatch(/text\/html/);
    const text = await response.text();
    expect(text).toBe("<html><body>Hello</body></html>");
  });

  it("reads the resolved html_path stored on the artifact row", async () => {
    const storedPath = htmlPath("path-check.html");
    insertArtifact(db, {
      slug: "path-check",
      title: "Path Check",
      html_path: storedPath,
    });
    mockExistsSync.mockReturnValue(true);
    mockReadFileSync.mockReturnValue("<p>content</p>");

    const req = new Request("http://localhost/api/artifacts/path-check/html");
    await GET(req as never, makeCtx("path-check"));

    expect(mockExistsSync).toHaveBeenCalledWith(path.resolve(storedPath));
    expect(mockReadFileSync).toHaveBeenCalledWith(path.resolve(storedPath), "utf-8");
  });

  // ── Error handling ─────────────────────────────────────────────────────────

  it("returns 500 when the database throws", async () => {
    mockGetDb.mockImplementation(() => {
      throw new Error("DB unavailable");
    });

    const req = new Request("http://localhost/api/artifacts/any/html");
    const response = await GET(req as never, makeCtx("any"));

    expect(response.status).toBe(500);
  });

  it("returns 500 when fs.readFileSync throws after existsSync returns true", async () => {
    insertArtifact(db, {
      slug: "read-error",
      title: "Read Error",
      html_path: htmlPath("broken.html"),
    });
    mockExistsSync.mockReturnValue(true);
    mockReadFileSync.mockImplementation(() => {
      throw new Error("EACCES: permission denied");
    });

    const req = new Request("http://localhost/api/artifacts/read-error/html");
    const response = await GET(req as never, makeCtx("read-error"));

    expect(response.status).toBe(500);
  });
});
