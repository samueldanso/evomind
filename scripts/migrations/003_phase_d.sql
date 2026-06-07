-- Migration 003 — Phase D — depends on artifacts table created by ingest.py _SCHEMA
-- (not a migration file). This is a known arrangement addressed in Phase H portability work.

CREATE TABLE IF NOT EXISTS agent_runs (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  agent_type    TEXT NOT NULL,
  task_input    TEXT NOT NULL,
  status        TEXT NOT NULL DEFAULT 'running',
  output        TEXT,
  error         TEXT,
  tool_calls    TEXT NOT NULL DEFAULT '[]',
  cost_tokens   INTEGER NOT NULL DEFAULT 0,
  cost_usd      REAL NOT NULL DEFAULT 0.0,
  started_at    TEXT NOT NULL,
  finished_at   TEXT
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_type   ON agent_runs(agent_type);
CREATE INDEX IF NOT EXISTS idx_agent_runs_status ON agent_runs(status);
