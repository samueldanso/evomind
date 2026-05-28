import Database from "better-sqlite3";
import os from "node:os";
import path from "node:path";

// Personal vault path — override with EVO_RESEARCH_STORE env var
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
  const store = process.env.EVO_RESEARCH_STORE ?? DEFAULT_STORE;
  return path.join(store, "manifest.db");
}

// Attach to globalThis so Next.js dev-mode HMR doesn't leak connections
const g = global as unknown as { _evoDB: Database.Database | undefined };

export function getDb(): Database.Database {
  if (!g._evoDB) {
    g._evoDB = new Database(resolveDbPath(), { readonly: true });
  }
  return g._evoDB;
}
