from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path

from backend.services.language_detect import detect_language

# Ensure we use the centralized data volume at /app/data
DB_PATH = Path("data/translation_memory.db")

_PRESERVE_TERMS_CACHE: list[dict] = []
_PRESERVE_TERMS_MTIME: float | None = None

# Module-level initialization flag for performance
_DB_INITIALIZED = False


def _load_preserve_terms() -> tuple[list[dict], float | None]:
    base_path = Path(__file__).parent.parent
    possible_paths = [
        base_path / "data" / "preserve_terms.json",
        Path("data/preserve_terms.json"),
    ]
    latest_mtime: float | None = None
    latest_terms: list[dict] = []
    for preserve_file in possible_paths:
        if not preserve_file.exists():
            continue
        try:
            stat = preserve_file.stat()
            if latest_mtime is None or stat.st_mtime > latest_mtime:
                with open(preserve_file, encoding="utf-8") as f:
                    latest_terms = json.load(f)
                latest_mtime = stat.st_mtime
        except Exception:
            continue
    return latest_terms, latest_mtime


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
                "SELECT id, source_lang, target_lang, source_text, "
                "target_text, priority, created_at "
                "FROM glossary ORDER BY priority DESC, id ASC LIMIT ?"
            ),
            (limit,),
        )
        rows = cur.fetchall()
        delete_ids: list[int] = []
        updates: list[tuple[str, int]] = []
        for row in rows:
            entry_id, source_lang, _, source_text, _, _, _ = row
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
        if updates:
            conn.executemany(
                "UPDATE glossary SET source_lang = ? WHERE id = ?",
                updates,
            )
            conn.commit()
            update_map = {entry_id: lang for lang, entry_id in updates}
        else:
            update_map = {}
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
            "created_at": row[6],
        }
        for row in rows
        if row[0] not in delete_ids
    ]


def get_tm(limit: int = 200) -> list[dict]:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            (
                "SELECT id, source_lang, target_lang, source_text, "
                "target_text, created_at FROM tm ORDER BY id DESC LIMIT ?"
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
            "created_at": row[5],
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
                "target_text, priority) "
                "VALUES (?, ?, ?, ?, COALESCE(?, 0))"
            ),
            (
                entry.get("source_lang"),
                entry.get("target_lang"),
                entry_source,
                entry_target,
                entry.get("priority", 0),
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
                    "target_text, priority) "
                    "VALUES (?, ?, ?, ?, COALESCE(?, 0))"
                ),
                (
                    entry.get("source_lang"),
                    entry.get("target_lang"),
                    entry_source,
                    entry_target,
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
