from __future__ import annotations

import hashlib
import sqlite3
from collections.abc import Iterable
from pathlib import Path

from backend.services.language_detect import detect_language
from backend.services.preserve_terms_repository import list_preserve_terms

# Ensure we use the centralized data volume at /app/data
DB_PATH = Path("data/translation_memory.db")

_PRESERVE_TERMS_CACHE: list[dict] = []
_PRESERVE_TERMS_MTIME: float | None = None

# Module-level initialization flag for performance
_DB_INITIALIZED = False


def _load_preserve_terms() -> tuple[list[dict], float | None]:
    db_path = Path("data/translation_memory.db")
    try:
        mtime = db_path.stat().st_mtime if db_path.exists() else None
    except Exception:
        mtime = None
    try:
        terms = list_preserve_terms()
    except Exception:
        terms = []
    return terms, mtime


def _get_preserve_terms() -> list[dict]:
    global _PRESERVE_TERMS_CACHE, _PRESERVE_TERMS_MTIME
    terms, mtime = _load_preserve_terms()
    if mtime is None:
        _PRESERVE_TERMS_CACHE = []
        _PRESERVE_TERMS_MTIME = None
        return _PRESERVE_TERMS_CACHE
    if _PRESERVE_TERMS_MTIME != mtime:
        _PRESERVE_TERMS_CACHE = terms
        _PRESERVE_TERMS_MTIME = mtime
    return _PRESERVE_TERMS_CACHE


def _is_preserve_term(text: str, terms: list[dict]) -> bool:
    if not text:
        return False
    text_clean = text.strip()
    if not text_clean:
        return False
    for term_entry in terms:
        term = (term_entry.get("term") or "").strip()
        if not term:
            continue
        case_sensitive = term_entry.get("case_sensitive", True)
        if case_sensitive:
            if text_clean == term:
                return True
        else:
            if text_clean.lower() == term.lower():
                return True
    return False


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
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tm (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_lang TEXT NOT NULL,
  target_lang TEXT NOT NULL,
  source_text TEXT NOT NULL,
  target_text TEXT NOT NULL,
  category_id INTEGER,
  hash TEXT NOT NULL UNIQUE,
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
            
        cursor = conn.execute("PRAGMA table_info(tm)")
        columns = [row[1] for row in cursor.fetchall()]
        if "category_id" not in columns:
            conn.execute("ALTER TABLE tm ADD COLUMN category_id INTEGER")

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
    _DB_INITIALIZED = True


def _hash_text(
    source_lang: str,
    target_lang: str,
    text: str,
    context: dict | None = None,
) -> str:
    payload = f"{source_lang}|{target_lang}|{text}"
    if context:
        ctx_str = "|".join(
            str(context.get(k, ""))
            for k in ["provider", "model", "tone"]
        )
        payload += f"||{ctx_str}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalize_glossary_text(text: str | None) -> str:
    if not text:
        return ""
    return " ".join(text.strip().split())


def lookup_tm(
    source_lang: str,
    target_lang: str,
    text: str,
    context: dict | None = None,
) -> str | None:
    _ensure_db()
    key = _hash_text(source_lang, target_lang, text, context=context)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("SELECT target_text FROM tm WHERE hash = ?", (key,))
        row = cur.fetchone()
    return row[0] if row else None


def save_tm(
    source_lang: str,
    target_lang: str,
    text: str,
    translated: str,
    context: dict | None = None,
) -> None:
    if not text or not translated:
        return
    _ensure_db()
    source_text = text.strip()
    target_text = translated.strip()
    if not source_text or not target_text:
        return
    preserve_terms = _get_preserve_terms()
    if _is_preserve_term(source_text, preserve_terms):
        return
    key = _hash_text(source_lang, target_lang, text, context=context)
    with sqlite3.connect(DB_PATH) as conn:
        normalized_source = _normalize_glossary_text(source_text)
        cur = conn.execute(
            (
                "SELECT 1 FROM glossary "
                "WHERE source_lang = ? AND target_lang = ? AND source_text = ? "
                "LIMIT 1"
            ),
            (source_lang, target_lang, normalized_source),
        )
        if cur.fetchone():
            return
        cur = conn.execute(
            "SELECT 1 FROM tm WHERE source_text = ? AND target_text = ? LIMIT 1",
            (source_text, target_text),
        )
        if cur.fetchone():
            return
        conn.execute(
            (
                "INSERT OR REPLACE INTO tm "
                "(source_lang, target_lang, source_text, target_text, hash) "
                "VALUES (?, ?, ?, ?, ?)"
            ),
            (source_lang, target_lang, text, translated, key),
        )
        conn.commit()


def apply_glossary(source_lang: str, target_lang: str, text: str) -> str:
    if not text:
        return text
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "SELECT source_text, target_text FROM glossary "
            "WHERE source_lang = ? AND target_lang = ? "
            "ORDER BY priority DESC, id ASC",
            (source_lang, target_lang),
        )
        rows = cur.fetchall()
    updated = text
    for source_text, target_text in rows:
        updated = updated.replace(source_text, target_text)
    return updated


def get_glossary_terms(
    source_lang: str,
    target_lang: str,
) -> list[tuple[str, str]]:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "SELECT source_text, target_text FROM glossary "
            "WHERE source_lang = ? AND target_lang = ? "
            "ORDER BY priority DESC, id ASC",
            (source_lang, target_lang),
        )
        rows = cur.fetchall()
    return [(row[0], row[1]) for row in rows]


def get_glossary_terms_any(target_lang: str) -> list[tuple[str, str]]:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "SELECT source_text, target_text FROM glossary "
            "WHERE target_lang = ? "
            "ORDER BY priority DESC, id ASC",
            (target_lang,),
        )
        rows = cur.fetchall()
    return [(row[0], row[1]) for row in rows]


def get_tm_terms(
    source_lang: str,
    target_lang: str,
    limit: int = 200,
) -> list[tuple[str, str]]:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "SELECT source_text, target_text FROM tm "
            "WHERE source_lang = ? AND target_lang = ? "
            "ORDER BY id DESC LIMIT ?",
            (source_lang, target_lang, limit),
        )
        rows = cur.fetchall()
    return [(row[0], row[1]) for row in rows]


def get_tm_terms_any(
    target_lang: str,
    limit: int = 200,
) -> list[tuple[str, str]]:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "SELECT source_text, target_text FROM tm "
            "WHERE target_lang = ? "
            "ORDER BY id DESC LIMIT ?",
            (target_lang, limit),
        )
        rows = cur.fetchall()
    return [(row[0], row[1]) for row in rows]


def seed_glossary(
    entries: Iterable[tuple[str, str, str, str, int | None]],
) -> None:
    _ensure_db()
    preserve_terms = _get_preserve_terms()
    with sqlite3.connect(DB_PATH) as conn:
        for (
            source_lang,
            target_lang,
            source_text,
            target_text,
            priority,
        ) in entries:
            source_text = _normalize_glossary_text(source_text)
            if _is_preserve_term(source_text, preserve_terms):
                continue
            conn.execute(
                (
                    "DELETE FROM glossary "
                    "WHERE source_lang = ? AND target_lang = ? "
                    "AND source_text = ?"
                ),
                (source_lang, target_lang, source_text),
            )
            conn.execute(
                (
                    "INSERT INTO glossary "
                    "(source_lang, target_lang, source_text, "
                    "target_text, priority) "
                    "VALUES (?, ?, ?, ?, COALESCE(?, 0))"
                ),
                (
                    source_lang,
                    target_lang,
                    source_text,
                    _normalize_glossary_text(target_text),
                    priority,
                ),
            )
        conn.commit()


def seed_tm(entries: Iterable[tuple[str, str, str, str]]) -> None:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        for source_lang, target_lang, source_text, target_text in entries:
            key = _hash_text(source_lang, target_lang, source_text)
            conn.execute(
                (
                    "INSERT OR REPLACE INTO tm "
                    "(source_lang, target_lang, source_text, "
                    "target_text, hash) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                (source_lang, target_lang, source_text, target_text, key),
            )
        conn.commit()


def get_glossary(limit: int = 200) -> list[dict]:
    _ensure_db()
    preserve_terms = _get_preserve_terms()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            (
                "SELECT g.id, g.source_lang, g.target_lang, g.source_text, "
                "g.target_text, g.priority, g.category_id, c.name as category_name, g.created_at "
                "FROM glossary g LEFT JOIN tm_categories c ON g.category_id = c.id "
                "ORDER BY g.priority DESC, g.id ASC LIMIT ?"
            ),
            (limit,),
        )
        rows = cur.fetchall()
        delete_ids: list[int] = []
        updates: list[tuple[str, int]] = []
        for row in rows:
            entry_id, source_lang, _, source_text, _, _, _, _, _ = row
            if _is_preserve_term(source_text, preserve_terms):
                delete_ids.append(entry_id)
                continue
            if not source_lang or source_lang in {"auto", "unknown"}:
                detected = detect_language(source_text or "")
                if detected and detected != source_lang:
                    updates.append((detected, entry_id))
        if delete_ids:
            conn.executemany(
                "DELETE FROM glossary WHERE id = ?",
                [(entry_id,) for entry_id in delete_ids],
            )
        update_map = {}
        if updates:
            for lang, entry_id in updates:
                row = conn.execute(
                    "SELECT source_text, target_lang FROM glossary WHERE id = ?",
                    (entry_id,),
                ).fetchone()
                if not row:
                    continue
                source_text, target_lang = row
                duplicate = conn.execute(
                    (
                        "SELECT id FROM glossary "
                        "WHERE source_lang = ? AND target_lang = ? AND source_text = ? "
                        "AND id != ? LIMIT 1"
                    ),
                    (lang, target_lang, source_text, entry_id),
                ).fetchone()
                if duplicate:
                    conn.execute("DELETE FROM glossary WHERE id = ?", (entry_id,))
                    delete_ids.append(entry_id)
                    continue
                conn.execute(
                    "UPDATE glossary SET source_lang = ? WHERE id = ?",
                    (lang, entry_id),
                )
                update_map[entry_id] = lang
            conn.commit()
        if delete_ids and not updates:
            conn.commit()
    return [
        {
            "id": row[0],
            "source_lang": update_map.get(row[0], row[1]),
            "target_lang": row[2],
            "source_text": row[3],
            "target_text": row[4],
            "priority": row[5],
            "category_id": row[6],
            "category_name": row[7],
            "created_at": row[8],
        }
        for row in rows
        if row[0] not in delete_ids
    ]


def get_tm(limit: int = 200) -> list[dict]:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            (
                "SELECT t.id, t.source_lang, t.target_lang, t.source_text, "
                "t.target_text, t.category_id, c.name as category_name, t.created_at "
                "FROM tm t LEFT JOIN tm_categories c ON t.category_id = c.id "
                "ORDER BY t.id DESC LIMIT ?"
            ),
            (limit,),
        )
        rows = cur.fetchall()
    return [
        {
            "id": row[0],
            "source_lang": row[1],
            "target_lang": row[2],
            "source_text": row[3],
            "target_text": row[4],
            "category_id": row[5],
            "category_name": row[6],
            "created_at": row[7],
        }
        for row in rows
    ]


def get_glossary_count() -> int:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("SELECT COUNT(1) FROM glossary")
        row = cur.fetchone()
    return int(row[0] or 0)


def get_tm_count() -> int:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("SELECT COUNT(1) FROM tm")
        row = cur.fetchone()
    return int(row[0] or 0)


def upsert_glossary(entry: dict) -> None:
    _ensure_db()
    preserve_terms = _get_preserve_terms()
    entry_source = _normalize_glossary_text(entry.get("source_text", ""))
    entry_target = _normalize_glossary_text(entry.get("target_text", ""))
    if _is_preserve_term(entry_source, preserve_terms):
        return
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            (
                "DELETE FROM glossary "
                "WHERE source_lang = ? AND target_lang = ? AND source_text = ?"
            ),
            (
                entry.get("source_lang"),
                entry.get("target_lang"),
                entry_source,
            ),
        )
        conn.execute(
            (
                "INSERT INTO glossary "
                "(source_lang, target_lang, source_text, "
                "target_text, priority, category_id) "
                "VALUES (?, ?, ?, ?, COALESCE(?, 0), ?)"
            ),
            (
                entry.get("source_lang"),
                entry.get("target_lang"),
                entry_source,
                entry_target,
                entry.get("priority", 0),
                entry.get("category_id"),
            ),
        )
        conn.commit()


def batch_upsert_glossary(entries: list[dict]) -> None:
    if not entries:
        return
    _ensure_db()
    preserve_terms = _get_preserve_terms()
    with sqlite3.connect(DB_PATH) as conn:
        for entry in entries:
            entry_source = _normalize_glossary_text(entry.get("source_text", ""))
            entry_target = _normalize_glossary_text(entry.get("target_text", ""))
            if _is_preserve_term(entry_source, preserve_terms):
                continue
            conn.execute(
                (
                    "DELETE FROM glossary "
                    "WHERE source_lang = ? AND target_lang = ? "
                    "AND source_text = ?"
                ),
                (
                    entry.get("source_lang"),
                    entry.get("target_lang"),
                    entry_source,
                ),
            )
            conn.execute(
                (
                    "INSERT INTO glossary "
                    "(source_lang, target_lang, source_text, "
                    "target_text, priority, category_id) "
                    "VALUES (?, ?, ?, ?, COALESCE(?, 0), ?)"
                ),
                (
                    entry.get("source_lang"),
                    entry.get("target_lang"),
                    entry_source,
                    entry_target,
                    entry.get("priority", 0),
                    entry.get("category_id"),
                ),
            )
        conn.commit()


def clear_glossary() -> int:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("DELETE FROM glossary")
        conn.commit()
        return cur.rowcount


def delete_glossary(entry_id: int) -> int:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "DELETE FROM glossary WHERE id = ?",
            (entry_id,),
        )
        conn.commit()
        return cur.rowcount


def batch_delete_glossary(ids: list[int]) -> int:
    if not ids:
        return 0
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        # Use executemany for efficiency
        cur = conn.executemany(
            "DELETE FROM glossary WHERE id = ?",
            [(entry_id,) for entry_id in ids],
        )
        conn.commit()
        return cur.rowcount


def upsert_tm(entry: dict) -> None:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        key = _hash_text(
            entry.get("source_lang"),
            entry.get("target_lang"),
            entry.get("source_text"),
        )
        conn.execute(
            (
                "INSERT OR REPLACE INTO tm "
                "(source_lang, target_lang, source_text, target_text, category_id, hash) "
                "VALUES (?, ?, ?, ?, ?, ?)"
            ),
            (
                entry.get("source_lang"),
                entry.get("target_lang"),
                entry.get("source_text"),
                entry.get("target_text"),
                entry.get("category_id"),
                key,
            ),
        )
        conn.commit()


def delete_tm(entry_id: int) -> int:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "DELETE FROM tm WHERE id = ?",
            (entry_id,),
        )
        conn.commit()
        return cur.rowcount


def batch_delete_tm(ids: list[int]) -> int:
    if not ids:
        return 0
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.executemany(
            "DELETE FROM tm WHERE id = ?",
            [(entry_id,) for entry_id in ids],
        )
        conn.commit()
        return cur.rowcount


def clear_tm() -> int:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("DELETE FROM tm")
        conn.commit()
        return cur.rowcount


# TM Categories functions

def list_tm_categories() -> list[dict]:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        # Get counts from glossary and tm tables
        query = """
            SELECT 
                c.id, 
                c.name, 
                c.sort_order,
                (SELECT COUNT(*) FROM glossary g WHERE g.category_id = c.id) as glossary_count,
                (SELECT COUNT(*) FROM tm t WHERE t.category_id = c.id) as tm_count
            FROM tm_categories c
            ORDER BY c.sort_order, c.id
        """
        rows = conn.execute(query).fetchall()
    return [dict(row) for row in rows]


def create_tm_category(name: str, sort_order: int | None = None) -> dict:
    _ensure_db()
    name = name.strip()
    if not name:
        raise ValueError("分類名稱不可為空")
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "INSERT INTO tm_categories (name, sort_order) VALUES (?, ?)",
            (name, sort_order or 0),
        )
        conn.commit()
        return {"id": cur.lastrowid, "name": name, "sort_order": sort_order or 0}


def update_tm_category(category_id: int, name: str, sort_order: int | None = None) -> dict:
    _ensure_db()
    name = name.strip()
    if not name:
        raise ValueError("分類名稱不可為空")
    with sqlite3.connect(DB_PATH) as conn:
        # Get old name for syncing
        old_row = conn.execute("SELECT name FROM tm_categories WHERE id = ?", (category_id,)).fetchone()
        old_name = old_row[0] if old_row else None

        conn.execute(
            "UPDATE tm_categories SET name = ?, sort_order = ? WHERE id = ?",
            (name, sort_order or 0, category_id),
        )
        
        if old_name and old_name != name:
            # Sync to preserve_terms in same DB
            conn.execute("UPDATE preserve_terms SET category = ? WHERE category = ?", (name, old_name))
            
            # Sync to terms.db if exists
            terms_db = Path("data/terms.db")
            if terms_db.exists():
                try:
                    with sqlite3.connect(terms_db) as tconn:
                        tconn.execute("UPDATE categories SET name = ? WHERE name = ?", (name, old_name))
                        tconn.commit()
                except Exception as e:
                    print(f"Error syncing to terms.db: {e}")
                    
        conn.commit()
        return {"id": category_id, "name": name, "sort_order": sort_order or 0}


def delete_tm_category(category_id: int) -> None:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        # Get name for syncing
        row = conn.execute("SELECT name FROM tm_categories WHERE id = ?", (category_id,)).fetchone()
        name = row[0] if row else None
        
        # Update items to NULL
        conn.execute("UPDATE glossary SET category_id = NULL WHERE category_id = ?", (category_id,))
        conn.execute("UPDATE tm SET category_id = NULL WHERE category_id = ?", (category_id,))
        
        if name:
            # Sync to preserve_terms: set back to '未分類' string
            conn.execute("UPDATE preserve_terms SET category = '未分類' WHERE category = ?", (name,))
            
            # Sync to terms.db Categories table
            terms_db = Path("data/terms.db")
            if terms_db.exists():
                try:
                    with sqlite3.connect(terms_db) as tconn:
                        # Find the corresponding category in terms.db by name
                        trow = tconn.execute("SELECT id FROM categories WHERE name = ?", (name,)).fetchone()
                        if trow:
                            tid = trow[0]
                            # Update terms in terms.db to NULL
                            tconn.execute("UPDATE terms SET category_id = NULL WHERE category_id = ?", (tid,))
                            tconn.execute("DELETE FROM categories WHERE id = ?", (tid,))
                            tconn.commit()
                except Exception as e:
                    print(f"Error syncing delete to terms.db: {e}")

        conn.execute("DELETE FROM tm_categories WHERE id = ?", (category_id,))
        conn.commit()
