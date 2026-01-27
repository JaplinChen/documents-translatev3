from __future__ import annotations

import hashlib
import sqlite3
from collections.abc import Iterable
from pathlib import Path

# Ensure we use the centralized data volume at /app/data
DB_PATH = Path("data/translation_memory.db")

# Module-level initialization flag for performance
_DB_INITIALIZED = False


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS glossary (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_lang TEXT NOT NULL,
  target_lang TEXT NOT NULL,
  source_text TEXT NOT NULL,
  target_text TEXT NOT NULL,
  priority INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tm (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_lang TEXT NOT NULL,
  target_lang TEXT NOT NULL,
  source_text TEXT NOT NULL,
  target_text TEXT NOT NULL,
  hash TEXT NOT NULL UNIQUE,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def _ensure_db() -> None:
    """Initialize DB once per process and re-init if the file is missing."""
    global _DB_INITIALIZED
    # Check if we think we are initialized and the file exists on disk.
    # If the file was deleted (e.g. by a cache reset), we MUST re-initialize.
    if _DB_INITIALIZED and DB_PATH.exists():
        return

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA_SQL)
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
    if not text:
        return
    _ensure_db()
    key = _hash_text(source_lang, target_lang, text, context=context)
    with sqlite3.connect(DB_PATH) as conn:
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
    with sqlite3.connect(DB_PATH) as conn:
        for (
            source_lang,
            target_lang,
            source_text,
            target_text,
            priority,
        ) in entries:
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
                    target_text,
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
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            (
                "SELECT id, source_lang, target_lang, source_text, "
                "target_text, priority "
                "FROM glossary ORDER BY priority DESC, id ASC LIMIT ?"
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
            "priority": row[5],
        }
        for row in rows
    ]


def get_tm(limit: int = 200) -> list[dict]:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            (
                "SELECT id, source_lang, target_lang, source_text, "
                "target_text FROM tm ORDER BY id DESC LIMIT ?"
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
        }
        for row in rows
    ]


def upsert_glossary(entry: dict) -> None:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            (
                "DELETE FROM glossary "
                "WHERE source_lang = ? AND target_lang = ? AND source_text = ?"
            ),
            (
                entry.get("source_lang"),
                entry.get("target_lang"),
                entry.get("source_text"),
            ),
        )
        conn.execute(
            (
                "INSERT INTO glossary "
                "(source_lang, target_lang, source_text, "
                "target_text, priority) "
                "VALUES (?, ?, ?, ?, COALESCE(?, 0))"
            ),
            (
                entry.get("source_lang"),
                entry.get("target_lang"),
                entry.get("source_text"),
                entry.get("target_text"),
                entry.get("priority", 0),
            ),
        )
        conn.commit()


def batch_upsert_glossary(entries: list[dict]) -> None:
    if not entries:
        return
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        for entry in entries:
            conn.execute(
                (
                    "DELETE FROM glossary "
                    "WHERE source_lang = ? AND target_lang = ? "
                    "AND source_text = ?"
                ),
                (
                    entry.get("source_lang"),
                    entry.get("target_lang"),
                    entry.get("source_text"),
                ),
            )
            conn.execute(
                (
                    "INSERT INTO glossary "
                    "(source_lang, target_lang, source_text, "
                    "target_text, priority) "
                    "VALUES (?, ?, ?, ?, COALESCE(?, 0))"
                ),
                (
                    entry.get("source_lang"),
                    entry.get("target_lang"),
                    entry.get("source_text"),
                    entry.get("target_text"),
                    entry.get("priority", 0),
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
                "(source_lang, target_lang, source_text, target_text, hash) "
                "VALUES (?, ?, ?, ?, ?)"
            ),
            (
                entry.get("source_lang"),
                entry.get("target_lang"),
                entry.get("source_text"),
                entry.get("target_text"),
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
