-- Migration 004 — Phase D.1 — add session_log for interactive teaching sessions

ALTER TABLE agent_runs ADD COLUMN session_log TEXT;
