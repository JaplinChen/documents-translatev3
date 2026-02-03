from __future__ import annotations

import sqlite3
from pathlib import Path

# Ensure we use the centralized data volume at /app/data
DB_PATH = Path("data/translation_memory.db")

# Module-level initialization flag for performance
_DB_INITIALIZED = False

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tm_categories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  sort_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS glossary (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_lang TEXT NOT NULL,
  target_lang TEXT NOT NULL,
  source_text TEXT NOT NULL,
  target_text TEXT NOT NULL,
  priority INTEGER DEFAULT 0,
  category_id INTEGER,
  domain TEXT,
  category TEXT,
  scope_type TEXT DEFAULT 'project',
  scope_id TEXT,
  status TEXT DEFAULT 'active',
  hit_count INTEGER DEFAULT 0,
  overwrite_count INTEGER DEFAULT 0,
  last_hit_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tm (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_lang TEXT NOT NULL,
  target_lang TEXT NOT NULL,
  source_text TEXT NOT NULL,
  target_text TEXT NOT NULL,
  category_id INTEGER,
  domain TEXT,
  category TEXT,
  scope_type TEXT DEFAULT 'project',
  scope_id TEXT,
  status TEXT DEFAULT 'active',
  hit_count INTEGER DEFAULT 0,
  overwrite_count INTEGER DEFAULT 0,
  last_hit_at TEXT,
  hash TEXT NOT NULL UNIQUE,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS term_feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_text TEXT NOT NULL,
  target_text TEXT NOT NULL,
  source_lang TEXT,
  target_lang TEXT,
  correction_count INTEGER DEFAULT 1,
  last_corrected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(source_text, target_text, source_lang, target_lang)
);

CREATE TABLE IF NOT EXISTS learning_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_type TEXT NOT NULL,
  scope_type TEXT DEFAULT 'project',
  scope_id TEXT,
  entity_type TEXT,
  entity_id INTEGER,
  source_text TEXT,
  target_text TEXT,
  source_lang TEXT,
  target_lang TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS learning_stats (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  stat_date TEXT NOT NULL,
  scope_type TEXT DEFAULT 'project',
  scope_id TEXT,
  tm_hit_rate REAL,
  glossary_hit_rate REAL,
  overwrite_rate REAL,
  auto_promotion_error_rate REAL,
  wrong_suggestion_rate REAL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def _ensure_db() -> None:
    """Initialize DB once per process and re-init if the file is missing."""
    global _DB_INITIALIZED
    if _DB_INITIALIZED and DB_PATH.exists():
        return

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA_SQL)

        # Migration: Add category_id if missing
        cursor = conn.execute("PRAGMA table_info(glossary)")
        columns = [row[1] for row in cursor.fetchall()]
        if "category_id" not in columns:
            conn.execute("ALTER TABLE glossary ADD COLUMN category_id INTEGER")
        if "domain" not in columns:
            conn.execute("ALTER TABLE glossary ADD COLUMN domain TEXT")
        if "category" not in columns:
            conn.execute("ALTER TABLE glossary ADD COLUMN category TEXT")
        if "scope_type" not in columns:
            conn.execute("ALTER TABLE glossary ADD COLUMN scope_type TEXT DEFAULT 'project'")
        if "scope_id" not in columns:
            conn.execute("ALTER TABLE glossary ADD COLUMN scope_id TEXT")
        if "status" not in columns:
            conn.execute("ALTER TABLE glossary ADD COLUMN status TEXT DEFAULT 'active'")
        if "hit_count" not in columns:
            conn.execute("ALTER TABLE glossary ADD COLUMN hit_count INTEGER DEFAULT 0")
        if "overwrite_count" not in columns:
            conn.execute("ALTER TABLE glossary ADD COLUMN overwrite_count INTEGER DEFAULT 0")
        if "last_hit_at" not in columns:
            conn.execute("ALTER TABLE glossary ADD COLUMN last_hit_at TEXT")

        cursor = conn.execute("PRAGMA table_info(tm)")
        columns = [row[1] for row in cursor.fetchall()]
        if "category_id" not in columns:
            conn.execute("ALTER TABLE tm ADD COLUMN category_id INTEGER")
        if "domain" not in columns:
            conn.execute("ALTER TABLE tm ADD COLUMN domain TEXT")
        if "category" not in columns:
            conn.execute("ALTER TABLE tm ADD COLUMN category TEXT")
        if "scope_type" not in columns:
            conn.execute("ALTER TABLE tm ADD COLUMN scope_type TEXT DEFAULT 'project'")
        if "scope_id" not in columns:
            conn.execute("ALTER TABLE tm ADD COLUMN scope_id TEXT")
        if "status" not in columns:
            conn.execute("ALTER TABLE tm ADD COLUMN status TEXT DEFAULT 'active'")
        if "hit_count" not in columns:
            conn.execute("ALTER TABLE tm ADD COLUMN hit_count INTEGER DEFAULT 0")
        if "overwrite_count" not in columns:
            conn.execute("ALTER TABLE tm ADD COLUMN overwrite_count INTEGER DEFAULT 0")
        if "last_hit_at" not in columns:
            conn.execute("ALTER TABLE tm ADD COLUMN last_hit_at TEXT")

        # Deduplicate existing glossary rows before adding unique index.
        conn.execute(
            "DELETE FROM glossary "
            "WHERE id NOT IN ("
            "  SELECT MAX(id) FROM glossary "
            "  GROUP BY source_lang, target_lang, source_text"
            ")"
        )
        # Enforce uniqueness by source/target/source_text.
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS "
            "idx_glossary_unique "
            "ON glossary (source_lang, target_lang, source_text)"
        )

        # Performance: Add indexes for category lookup and count
        conn.execute("CREATE INDEX IF NOT EXISTS idx_glossary_category ON glossary (category_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tm_category ON tm (category_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tm_scope ON tm (scope_type, scope_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_glossary_scope ON glossary (scope_type, scope_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_le_event_type ON learning_events (event_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_le_scope ON learning_events (scope_type, scope_id)")
    _DB_INITIALIZED = True
