import Database from "better-sqlite3";
import os from "node:os";
import path from "node:path";

const DEFAULT_STORE = path.join(
  os.homedir(),
  "Library",
  "Mobile Documents",
  "iCloud~md~obsidian",
  "Documents",
  "Samuel's Vault",
  "HomeOS",
  "Knowledge",
  "Research",
);

function resolveDbPath(): string {
  const env = process.env.EVO_RESEARCH_STORE;
  const store = env ? env : DEFAULT_STORE;
  return path.join(store, "manifest.db");
}

let _db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!_db) {
    _db = new Database(resolveDbPath(), { readonly: true });
  }
  return _db;
}
