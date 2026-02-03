from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path("data/terms.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS categories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  sort_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS terms (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  term TEXT NOT NULL,
  term_norm TEXT NOT NULL,
  category_id INTEGER,
  status TEXT NOT NULL,
  target_lang TEXT,
  case_rule TEXT,
  note TEXT,
  source TEXT,
  source_lang TEXT,
  priority INTEGER DEFAULT 0,
  filename TEXT,
  created_by TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS term_languages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  term_id INTEGER NOT NULL,
  lang_code TEXT NOT NULL,
  value TEXT,
  value_norm TEXT,
  UNIQUE(term_id, lang_code)
);

CREATE TABLE IF NOT EXISTS term_aliases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  term_id INTEGER NOT NULL,
  alias TEXT NOT NULL,
  alias_norm TEXT NOT NULL,
  UNIQUE(term_id, alias_norm)
);

CREATE TABLE IF NOT EXISTS term_versions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  term_id INTEGER NOT NULL,
  diff TEXT,
  created_by TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

_DB_INITIALIZED = False


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_db() -> None:
    global _DB_INITIALIZED
    if _DB_INITIALIZED and DB_PATH.exists():
        return
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.executescript(SCHEMA_SQL)
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_terms_norm ON terms (term_norm)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_term_lang_code ON term_languages (lang_code)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_term_alias_norm ON term_aliases (alias_norm)")
        cursor = conn.execute("PRAGMA table_info(terms)")
        columns = [row["name"] for row in cursor.fetchall()]
        if "priority" not in columns:
            conn.execute("ALTER TABLE terms ADD COLUMN priority INTEGER DEFAULT 0")
        if "source_lang" not in columns:
            conn.execute("ALTER TABLE terms ADD COLUMN source_lang TEXT")
        if "target_lang" not in columns:
            conn.execute("ALTER TABLE terms ADD COLUMN target_lang TEXT")
        if "case_rule" not in columns:
            conn.execute("ALTER TABLE terms ADD COLUMN case_rule TEXT DEFAULT 'preserve'")
        if "filename" not in columns:
            conn.execute("ALTER TABLE terms ADD COLUMN filename TEXT")
    _DB_INITIALIZED = True


def _normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return " ".join(text.strip().split())
