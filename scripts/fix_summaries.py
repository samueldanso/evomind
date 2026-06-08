#!/usr/bin/env python3
"""One-time retrofix: strip raw HTML/markdown fences from artifact summaries."""

import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.ingest import get_store_path


def clean_summary(summary: str) -> str:
    """Strip HTML tags, markdown fences, and collapse whitespace."""
    text = re.sub(r"```html\s*", "", summary)
    text = re.sub(r"```\s*", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 300:
        boundary = text.rfind(".", 0, 300)
        if boundary > 50:
            text = text[: boundary + 1]
        else:
            text = text[:300]
    return text


def fix_all(db: sqlite3.Connection) -> int:
    """Fix all artifact summaries containing HTML or markdown fences. Returns count fixed."""
    rows = db.execute(
        "SELECT id, summary FROM artifacts WHERE summary LIKE '%<%' OR summary LIKE '%```html%'"
    ).fetchall()

    fixed = 0
    for row_id, summary in rows:
        cleaned = clean_summary(summary)
        if cleaned != summary:
            db.execute("UPDATE artifacts SET summary = ? WHERE id = ?", (cleaned, row_id))
            fixed += 1

    if fixed:
        db.commit()
    return fixed


if __name__ == "__main__":
    store = get_store_path()
    db_path = store / "manifest.db"
    if not db_path.exists():
        print(f"No database at {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    count = fix_all(conn)
    print(f"Fixed {count} artifact summaries.")
    conn.close()
