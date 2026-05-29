-- Migration 002 — Phase C: Intelligence Layer
-- Adds chunks, embeddings (sqlite-vec), claims stub, and migration tracking.
-- Idempotent: safe to apply to a DB that already has these tables.

CREATE TABLE IF NOT EXISTS migrations (
  version    INTEGER PRIMARY KEY,
  applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  artifact_id INTEGER NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
  ordinal     INTEGER NOT NULL,
  text        TEXT NOT NULL,
  char_start  INTEGER NOT NULL,
  char_end    INTEGER NOT NULL,
  created_at  TEXT NOT NULL,
  UNIQUE(artifact_id, ordinal)
);

CREATE INDEX IF NOT EXISTS idx_chunks_artifact ON chunks(artifact_id);

CREATE VIRTUAL TABLE IF NOT EXISTS embeddings USING vec0(
  chunk_id  INTEGER PRIMARY KEY,
  embedding FLOAT[1536]
);

-- Stub for Phase E claim extraction — no rows written in Phase C.
CREATE TABLE IF NOT EXISTS claims (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  text          TEXT NOT NULL,
  canonical_id  INTEGER REFERENCES claims(id),
  confidence    REAL NOT NULL DEFAULT 0.0,
  superseded_by INTEGER REFERENCES claims(id),
  created_at    TEXT NOT NULL,
  updated_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS claim_sources (
  claim_id INTEGER NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
  chunk_id INTEGER NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
  PRIMARY KEY (claim_id, chunk_id)
);
