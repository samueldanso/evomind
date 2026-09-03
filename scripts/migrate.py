"""scripts/migrate.py — forward-only DB migration runner for EvoMind.

Usage:
    uv run scripts/migrate.py [--db PATH] [--skip-backup-check]
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
DEFAULT_VAULT = (
    Path.home()
    / "Library/Mobile Documents/iCloud~md~obsidian/Documents"
    / "Samuel's Vault/SamuelOS/Knowledge"
)


def _db_path_from_env() -> Path:
    env = os.environ.get("EVO_STORE")
    if env:
        return Path(env) / "manifest.db"
    return DEFAULT_VAULT / "manifest.db"


def check_backup(db_path: Path) -> None:
    """Error if manifest.db.bak is missing or older than manifest.db."""
    bak = db_path.with_suffix(".db.bak")
    if not bak.exists():
        print(
            f"ERROR: backup not found at {bak}. "
            "Run: cp manifest.db manifest.db.bak\n"
            "Or pass --skip-backup-check to bypass (CI only).",
            file=sys.stderr,
        )
        sys.exit(1)
    if bak.stat().st_mtime < db_path.stat().st_mtime:
        print(
            f"ERROR: {bak} is older than {db_path}. Re-run: cp manifest.db manifest.db.bak",
            file=sys.stderr,
        )
        sys.exit(1)


def _load_sqlite_vec(conn: sqlite3.Connection) -> None:
    """Load sqlite-vec extension; skip gracefully if unavailable in test env."""
    try:
        import sqlite_vec  # type: ignore[import-untyped]

        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
    except Exception:
        pass


def _version_from_filename(name: str) -> int | None:
    m = re.match(r"^(\d+)", name)
    return int(m.group(1)) if m else None


def apply_migrations(
    conn: sqlite3.Connection,
    migrations_dir: Path,
    skip_backup_check: bool = False,
) -> int:
    """Apply all pending migrations. Returns count of newly applied migrations."""
    _load_sqlite_vec(conn)

    # Ensure migrations table exists before checking it.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS migrations (
          version    INTEGER PRIMARY KEY,
          applied_at TEXT NOT NULL
        )
    """)
    conn.commit()

    sql_files = sorted(
        (f for f in migrations_dir.glob("*.sql")),
        key=lambda f: _version_from_filename(f.name) or 0,
    )

    applied = 0
    for sql_file in sql_files:
        version = _version_from_filename(sql_file.name)
        if version is None:
            continue

        row = conn.execute("SELECT 1 FROM migrations WHERE version = ?", (version,)).fetchone()
        if row:
            print(f"Migration {version:03d} already applied, skipping.")
            continue

        print(f"Applying migration {version:03d}...")
        sql = sql_file.read_text(encoding="utf-8")
        conn.executescript(sql)
        conn.execute(
            "INSERT INTO migrations (version, applied_at) VALUES (?, datetime('now'))",
            (version,),
        )
        conn.commit()
        applied += 1

    print(f"Done. {applied} migration(s) applied.")
    return applied


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="EvoMind DB migration runner")
    parser.add_argument("--db", type=Path, default=None, help="Path to manifest.db")
    parser.add_argument(
        "--skip-backup-check",
        action="store_true",
        default=False,
        help="Skip backup freshness check (CI only)",
    )
    args = parser.parse_args(argv)

    db_path = args.db or _db_path_from_env()

    if not args.skip_backup_check:
        check_backup(db_path)

    if not db_path.exists():
        print(f"ERROR: DB not found at {db_path}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        apply_migrations(conn, MIGRATIONS_DIR, skip_backup_check=args.skip_backup_check)
    except Exception as exc:
        print(f"ERROR: migration failed: {exc}", file=sys.stderr)
        conn.close()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
