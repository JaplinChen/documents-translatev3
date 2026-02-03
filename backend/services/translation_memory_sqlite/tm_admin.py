from __future__ import annotations

import sqlite3

from .db import DB_PATH, _ensure_db
from .learning import _record_learning_event
from .utils import _hash_text, _is_low_quality_tm


def upsert_tm(entry: dict) -> None:
    _ensure_db()

    source_text = entry.get("source_text", "").strip()
    target_text = entry.get("target_text", "").strip()

    if _is_low_quality_tm(source_text, target_text):
        print(f"攔截低質量 TM (Upsert): {source_text} -> {target_text}")
        return

    entry_id = entry.get("id")
    scope_type = entry.get("scope_type") or "project"
    scope_id = entry.get("scope_id") or "default"
    domain = entry.get("domain")
    category = entry.get("category")
    with sqlite3.connect(DB_PATH) as conn:
        existing = None
        if entry_id:
            existing = conn.execute(
                "SELECT target_text FROM tm WHERE id = ?",
                (entry_id,),
            ).fetchone()
        else:
            existing = conn.execute(
                "SELECT id, target_text FROM tm WHERE source_lang = ? AND target_lang = ? AND source_text = ?",
                (
                    entry.get("source_lang"),
                    entry.get("target_lang"),
                    entry.get("source_text"),
                ),
            ).fetchone()
        if existing:
            existing_id = entry_id or existing[0]
            existing_target = existing[0] if entry_id else existing[1]
            if existing_target != entry.get("target_text"):
                conn.execute(
                    "UPDATE tm SET overwrite_count = overwrite_count + 1 WHERE id = ?",
                    (existing_id,),
                )
                _record_learning_event(
                    "overwrite",
                    source_text=entry.get("source_text"),
                    target_text=entry.get("target_text"),
                    source_lang=entry.get("source_lang"),
                    target_lang=entry.get("target_lang"),
                    entity_type="tm",
                    entity_id=existing_id,
                    scope_type=scope_type,
                    scope_id=scope_id,
                )
        if entry_id:
            # Explicit update by ID
            conn.execute(
                (
                    "UPDATE tm SET "
                    "source_lang = ?, target_lang = ?, source_text = ?, "
                    "target_text = ?, category_id = ?, domain = ?, category = ?, "
                    "scope_type = ?, scope_id = ?, hash = ? "
                    "WHERE id = ?"
                ),
                (
                    entry.get("source_lang"),
                    entry.get("target_lang"),
                    entry.get("source_text"),
                    entry.get("target_text"),
                    entry.get("category_id"),
                    domain,
                    category,
                    scope_type,
                    scope_id,
                    _hash_text(
                        entry.get("source_lang"), entry.get("target_lang"), entry.get("source_text")
                    ),
                    entry_id,
                ),
            )
            print(f"TM updated by ID: {entry_id}")
        else:
            # Fallback to hash-based INSERT OR REPLACE
            key = _hash_text(
                entry.get("source_lang"),
                entry.get("target_lang"),
                entry.get("source_text"),
            )
            conn.execute(
                (
                    "INSERT OR REPLACE INTO tm "
                    "(source_lang, target_lang, source_text, target_text, "
                    "category_id, domain, category, scope_type, scope_id, hash) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                ),
                (
                    entry.get("source_lang"),
                    entry.get("target_lang"),
                    entry.get("source_text"),
                    entry.get("target_text"),
                    entry.get("category_id"),
                    domain,
                    category,
                    scope_type,
                    scope_id,
                    key,
                ),
            )
            print(f"TM upserted by hash: {entry.get('source_text')}")
        conn.commit()
    _record_learning_event(
        "ingest",
        source_text=entry.get("source_text"),
        target_text=entry.get("target_text"),
        source_lang=entry.get("source_lang"),
        target_lang=entry.get("target_lang"),
        entity_type="tm",
        entity_id=entry.get("id"),
        scope_type=scope_type,
        scope_id=scope_id,
    )


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
