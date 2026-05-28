/**
 * In-memory SQLite factory for API route tests.
 *
 * Creates the same schema as the real manifest.db (artifacts table + FTS5
 * virtual table) so route handlers run against a real SQL engine without
 * touching the vault on disk.
 */
import Database from "better-sqlite3";
import type { Artifact } from "@/lib/types";

export type TestArtifact = Omit<Artifact, "id">;

const SCHEMA = `
  CREATE TABLE IF NOT EXISTS artifacts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    slug       TEXT NOT NULL UNIQUE,
    title      TEXT NOT NULL,
    summary    TEXT,
    tags       TEXT NOT NULL DEFAULT '',
    topics     TEXT NOT NULL DEFAULT '',
    html_path  TEXT,
    md_path    TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
  );

  CREATE VIRTUAL TABLE IF NOT EXISTS artifacts_fts USING fts5(
    title,
    summary,
    tags,
    topics,
    content='artifacts',
    content_rowid='id'
  );

  CREATE TRIGGER IF NOT EXISTS artifacts_ai AFTER INSERT ON artifacts BEGIN
    INSERT INTO artifacts_fts(rowid, title, summary, tags, topics)
    VALUES (new.id, new.title, new.summary, new.tags, new.topics);
  END;
`;

/** Build a fresh in-memory DB ready for route handler injection. */
export function makeTestDb(): Database.Database {
  const db = new Database(":memory:");
  db.exec(SCHEMA);
  return db;
}

/**
 * Insert one artifact row and return the inserted row (with auto-assigned id).
 * Omit html_path / md_path to simulate an artifact with no HTML file.
 */
export function insertArtifact(
  db: Database.Database,
  partial: Partial<TestArtifact> & { slug: string; title: string }
): Artifact {
  const row = {
    slug: partial.slug,
    title: partial.title,
    summary: partial.summary ?? "A summary.",
    tags: partial.tags ?? "tag1,tag2",
    topics: partial.topics ?? "topic1",
    html_path: partial.html_path ?? null,
    md_path: partial.md_path ?? null,
    created_at: partial.created_at ?? new Date().toISOString(),
    updated_at: partial.updated_at ?? new Date().toISOString(),
  };

  const stmt = db.prepare(`
    INSERT INTO artifacts (slug, title, summary, tags, topics, html_path, md_path, created_at, updated_at)
    VALUES (@slug, @title, @summary, @tags, @topics, @html_path, @md_path, @created_at, @updated_at)
  `);
  const info = stmt.run(row);

  return db
    .prepare("SELECT * FROM artifacts WHERE id = ?")
    .get(info.lastInsertRowid) as Artifact;
}
