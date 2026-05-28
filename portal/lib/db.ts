import path from "node:path";
import Database from "better-sqlite3";
import { resolveVaultRoot } from "@/lib/path-guard";

function resolveDbPath(): string {
  return path.join(resolveVaultRoot(), "manifest.db");
}

// Attach to globalThis so Next.js dev-mode HMR doesn't leak connections
const g = global as unknown as { _evoDB: Database.Database | undefined };

export function getDb(): Database.Database {
  if (!g._evoDB) {
    const dbPath = resolveDbPath();
    // Don't cache a failed open — next request will retry
    const db = new Database(dbPath, { readonly: true });
    g._evoDB = db;
  }
  return g._evoDB;
}

/** Clear cached connection — called after DB is known to be missing so next request retries */
export function resetDb(): void {
  g._evoDB = undefined;
}
