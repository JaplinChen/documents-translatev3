from __future__ import annotations

from sqlalchemy import text

from backend.db.engine import get_engine

from .db import _ensure_db
from .learning import _record_learning_event
from .utils import _hash_text, _is_low_quality_tm


def upsert_tm(entry: dict) -> None:
    _ensure_db()

    source_text = entry.get("source_text", "").strip()
    target_text = entry.get("target_text", "").strip()

    if _is_low_quality_tm(source_text, target_text):
        return

    entry_id = entry.get("id")
    scope_type = entry.get("scope_type") or "project"
    scope_id = entry.get("scope_id") or "default"
    domain = entry.get("domain")
    category = entry.get("category")
    engine = get_engine()
    with engine.begin() as conn:
        existing = None
        if entry_id:
            existing = conn.execute(
                text("SELECT target_text FROM tm WHERE id = :id"),
                {"id": entry_id},
            ).fetchone()
        else:
            existing = conn.execute(
                text(
                    "SELECT id, target_text FROM tm "
                    "WHERE source_lang = :source_lang AND target_lang = :target_lang "
                    "AND source_text = :source_text"
                ),
                {
                    "source_lang": entry.get("source_lang"),
                    "target_lang": entry.get("target_lang"),
                    "source_text": entry.get("source_text"),
                },
            ).fetchone()
        if existing:
            existing_id = entry_id or existing[0]
            existing_target = existing[0] if entry_id else existing[1]
            if existing_target != entry.get("target_text"):
                conn.execute(
                    text("UPDATE tm SET overwrite_count = overwrite_count + 1 WHERE id = :id"),
                    {"id": existing_id},
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
            conn.execute(
                text(
                    "UPDATE tm SET "
                    "source_lang = :source_lang, target_lang = :target_lang, source_text = :source_text, "
                    "target_text = :target_text, category_id = :category_id, domain = :domain, "
                    "category = :category, scope_type = :scope_type, scope_id = :scope_id, hash = :hash "
                    "WHERE id = :id"
                ),
                {
                    "source_lang": entry.get("source_lang"),
                    "target_lang": entry.get("target_lang"),
                    "source_text": entry.get("source_text"),
                    "target_text": entry.get("target_text"),
                    "category_id": entry.get("category_id"),
                    "domain": domain,
                    "category": category,
                    "scope_type": scope_type,
                    "scope_id": scope_id,
                    "hash": _hash_text(
                        entry.get("source_lang"), entry.get("target_lang"), entry.get("source_text")
                    ),
                    "id": entry_id,
                },
            )
        else:
            key = _hash_text(
                entry.get("source_lang"),
                entry.get("target_lang"),
                entry.get("source_text"),
            )
            conn.execute(
                text(
                    "INSERT INTO tm "
                    "(source_lang, target_lang, source_text, target_text, "
                    "category_id, domain, category, scope_type, scope_id, hash, created_at) "
                    "VALUES (:source_lang, :target_lang, :source_text, :target_text, "
                    ":category_id, :domain, :category, :scope_type, :scope_id, :hash, now()) "
                    "ON CONFLICT (hash) DO UPDATE SET "
                    "target_text = EXCLUDED.target_text, category_id = EXCLUDED.category_id, "
                    "domain = EXCLUDED.domain, category = EXCLUDED.category, "
                    "scope_type = EXCLUDED.scope_type, scope_id = EXCLUDED.scope_id"
                ),
                {
                    "source_lang": entry.get("source_lang"),
                    "target_lang": entry.get("target_lang"),
                    "source_text": entry.get("source_text"),
                    "target_text": entry.get("target_text"),
                    "category_id": entry.get("category_id"),
                    "domain": domain,
                    "category": category,
                    "scope_type": scope_type,
                    "scope_id": scope_id,
                    "hash": key,
                },
            )
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
    engine = get_engine()
    with engine.begin() as conn:
        res = conn.execute(text("DELETE FROM tm WHERE id = :id"), {"id": entry_id})
    return res.rowcount or 0


def batch_delete_tm(ids: list[int]) -> int:
    if not ids:
        return 0
    _ensure_db()
    engine = get_engine()
    with engine.begin() as conn:
        res = conn.execute(text("DELETE FROM tm WHERE id = ANY(:ids)"), {"ids": ids})
    return res.rowcount or 0


def clear_tm() -> int:
    _ensure_db()
    engine = get_engine()
    with engine.begin() as conn:
        res = conn.execute(text("DELETE FROM tm"))
    return res.rowcount or 0
