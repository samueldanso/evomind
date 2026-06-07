"""Shared database utilities for EvoResearch."""

import os
import sqlite3
from pathlib import Path

_DEFAULT_STORE = (
    Path.home()
    / "Library"
    / "Mobile Documents"
    / "iCloud~md~obsidian"
    / "Documents"
    / "Samuel's Vault"
    / "HomeOS"
    / "Knowledge"
    / "Research"
)


def default_db_path() -> Path:
    env = os.environ.get("EVO_RESEARCH_STORE")
    store = Path(env) if env else _DEFAULT_STORE
    return store / "manifest.db"


def open_db(path: Path | None = None) -> sqlite3.Connection:
    db_path = path or default_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row
    return conn


def load_sqlite_vec(conn: sqlite3.Connection) -> None:
    try:
        import sqlite_vec  # type: ignore[import-untyped]

        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
    except Exception:
        pass
