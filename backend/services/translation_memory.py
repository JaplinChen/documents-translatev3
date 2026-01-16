from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Iterable


DB_PATH = Path(__file__).resolve().parents[2] / "data" / "translation_memory.db"


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
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA_SQL)


def _hash_text(source_lang: str, target_lang: str, text: str) -> str:
    payload = f"{source_lang}|{target_lang}|{text}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def lookup_tm(source_lang: str, target_lang: str, text: str) -> str | None:
    _ensure_db()
    key = _hash_text(source_lang, target_lang, text)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("SELECT target_text FROM tm WHERE hash = ?", (key,))
        row = cur.fetchone()
    return row[0] if row else None


def save_tm(source_lang: str, target_lang: str, text: str, translated: str) -> None:
    if not text:
        return
    _ensure_db()
    key = _hash_text(source_lang, target_lang, text)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO tm (source_lang, target_lang, source_text, target_text, hash) "
            "VALUES (?, ?, ?, ?, ?)",
            (source_lang, target_lang, text, translated, key),
        )
        conn.commit()


def apply_glossary(
    source_lang: str, target_lang: str, text: str
) -> str:
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


def get_glossary_terms(source_lang: str, target_lang: str) -> list[tuple[str, str]]:
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


def get_tm_terms(source_lang: str, target_lang: str, limit: int = 200) -> list[tuple[str, str]]:
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


def get_tm_terms_any(target_lang: str, limit: int = 200) -> list[tuple[str, str]]:
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


def seed_glossary(entries: Iterable[tuple[str, str, str, str, int | None]]) -> None:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.executemany(
            "INSERT INTO glossary (source_lang, target_lang, source_text, target_text, priority) "
            "VALUES (?, ?, ?, ?, COALESCE(?, 0))",
            entries,
        )
        conn.commit()


def seed_tm(entries: Iterable[tuple[str, str, str, str]]) -> None:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        for source_lang, target_lang, source_text, target_text in entries:
            key = _hash_text(source_lang, target_lang, source_text)
            conn.execute(
                "INSERT OR REPLACE INTO tm (source_lang, target_lang, source_text, target_text, hash) "
                "VALUES (?, ?, ?, ?, ?)",
                (source_lang, target_lang, source_text, target_text, key),
            )
        conn.commit()


def get_glossary(limit: int = 200) -> list[dict]:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "SELECT id, source_lang, target_lang, source_text, target_text, priority "
            "FROM glossary ORDER BY priority DESC, id ASC LIMIT ?",
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
            "SELECT id, source_lang, target_lang, source_text, target_text "
            "FROM tm ORDER BY id DESC LIMIT ?",
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
            "DELETE FROM glossary WHERE source_lang = ? AND target_lang = ? AND source_text = ?",
            (
                entry.get("source_lang"),
                entry.get("target_lang"),
                entry.get("source_text"),
            ),
        )
        conn.execute(
            "INSERT INTO glossary (source_lang, target_lang, source_text, target_text, priority) "
            "VALUES (?, ?, ?, ?, COALESCE(?, 0))",
            (
                entry.get("source_lang"),
                entry.get("target_lang"),
                entry.get("source_text"),
                entry.get("target_text"),
                entry.get("priority", 0),
            ),
        )
        conn.commit()


def delete_glossary(entry_id: int) -> int:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "DELETE FROM glossary WHERE id = ?",
            (entry_id,),
        )
        conn.commit()
        return cur.rowcount


def upsert_tm(entry: dict) -> None:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        key = _hash_text(
            entry.get("source_lang"), entry.get("target_lang"), entry.get("source_text")
        )
        conn.execute(
            "INSERT OR REPLACE INTO tm (source_lang, target_lang, source_text, target_text, hash) "
            "VALUES (?, ?, ?, ?, ?)",
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


def clear_tm() -> int:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("DELETE FROM tm")
        conn.commit()
        return cur.rowcount
