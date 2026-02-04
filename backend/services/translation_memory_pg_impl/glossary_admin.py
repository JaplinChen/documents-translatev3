from __future__ import annotations

from sqlalchemy import text

from backend.db.engine import get_engine
import backend.services.term_repository as term_repo

from .db import _ensure_db
from .preserve_terms import _get_preserve_terms, _is_preserve_term
from .utils import _normalize_glossary_text


def _get_tm_category_name(category_id: int | None) -> str | None:
    if not category_id:
        return None
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT name FROM tm_categories WHERE id = :id"),
            {"id": category_id},
        ).fetchone()
    return row[0] if row else None


def upsert_glossary(entry: dict) -> None:
    _ensure_db()
    preserve_terms = _get_preserve_terms()
    entry_source = _normalize_glossary_text(entry.get("source_text", ""))
    entry_target = _normalize_glossary_text(entry.get("target_text", ""))
    if _is_preserve_term(entry_source, preserve_terms):
        return
    entry_id = entry.get("id")
    engine = get_engine()
    with engine.begin() as conn:
        if entry_id:
            conn.execute(
                text(
                    "UPDATE glossary SET "
                    "source_lang = :source_lang, target_lang = :target_lang, source_text = :source_text, "
                    "target_text = :target_text, priority = :priority, category_id = :category_id, "
                    "domain = :domain, category = :category, scope_type = :scope_type, scope_id = :scope_id "
                    "WHERE id = :id"
                ),
                {
                    "source_lang": entry.get("source_lang"),
                    "target_lang": entry.get("target_lang"),
                    "source_text": entry_source,
                    "target_text": entry_target,
                    "priority": entry.get("priority", 0),
                    "category_id": entry.get("category_id"),
                    "domain": entry.get("domain"),
                    "category": entry.get("category"),
                    "scope_type": entry.get("scope_type") or "project",
                    "scope_id": entry.get("scope_id") or "default",
                    "id": entry_id,
                },
            )
        else:
            conn.execute(
                text(
                    "INSERT INTO glossary "
                    "(source_lang, target_lang, source_text, target_text, priority, "
                    "category_id, domain, category, scope_type, scope_id, created_at) "
                    "VALUES (:source_lang, :target_lang, :source_text, :target_text, :priority, "
                    ":category_id, :domain, :category, :scope_type, :scope_id, now()) "
                    "ON CONFLICT (source_lang, target_lang, source_text) DO UPDATE SET "
                    "target_text = EXCLUDED.target_text, priority = EXCLUDED.priority, "
                    "category_id = EXCLUDED.category_id, domain = EXCLUDED.domain, "
                    "category = EXCLUDED.category, scope_type = EXCLUDED.scope_type, scope_id = EXCLUDED.scope_id"
                ),
                {
                    "source_lang": entry.get("source_lang"),
                    "target_lang": entry.get("target_lang"),
                    "source_text": entry_source,
                    "target_text": entry_target,
                    "priority": entry.get("priority", 0),
                    "category_id": entry.get("category_id"),
                    "domain": entry.get("domain"),
                    "category": entry.get("category"),
                    "scope_type": entry.get("scope_type") or "project",
                    "scope_id": entry.get("scope_id") or "default",
                },
            )
    try:
        lang_code = entry.get("target_lang", "zh-TW")
        category_name = _get_tm_category_name(entry.get("category_id"))
        term_repo.sync_from_external(
            entry_source,
            category_name=category_name,
            source="reference",
            source_lang=entry.get("source_lang"),
            target_lang=entry.get("target_lang"),
            languages=[{"lang_code": lang_code, "value": entry_target}],
        )
    except Exception:
        return


def batch_upsert_glossary(entries: list[dict]) -> None:
    if not entries:
        return
    _ensure_db()
    preserve_terms = _get_preserve_terms()
    engine = get_engine()
    with engine.begin() as conn:
        for entry in entries:
            entry_source = _normalize_glossary_text(entry.get("source_text", ""))
            entry_target = _normalize_glossary_text(entry.get("target_text", ""))
            if _is_preserve_term(entry_source, preserve_terms):
                continue
            conn.execute(
                text(
                    "INSERT INTO glossary "
                    "(source_lang, target_lang, source_text, target_text, priority, "
                    "category_id, domain, category, scope_type, scope_id, created_at) "
                    "VALUES (:source_lang, :target_lang, :source_text, :target_text, :priority, "
                    ":category_id, :domain, :category, :scope_type, :scope_id, now()) "
                    "ON CONFLICT (source_lang, target_lang, source_text) DO UPDATE SET "
                    "target_text = EXCLUDED.target_text, priority = EXCLUDED.priority, "
                    "category_id = EXCLUDED.category_id, domain = EXCLUDED.domain, "
                    "category = EXCLUDED.category, scope_type = EXCLUDED.scope_type, scope_id = EXCLUDED.scope_id"
                ),
                {
                    "source_lang": entry.get("source_lang"),
                    "target_lang": entry.get("target_lang"),
                    "source_text": entry_source,
                    "target_text": entry_target,
                    "priority": entry.get("priority", 0),
                    "category_id": entry.get("category_id"),
                    "domain": entry.get("domain"),
                    "category": entry.get("category"),
                    "scope_type": entry.get("scope_type") or "project",
                    "scope_id": entry.get("scope_id") or "default",
                },
            )

    for entry in entries:
        try:
            entry_source = _normalize_glossary_text(entry.get("source_text", ""))
            entry_target = _normalize_glossary_text(entry.get("target_text", ""))
            lang_code = entry.get("target_lang", "zh-TW")
            category_name = _get_tm_category_name(entry.get("category_id"))
            term_repo.sync_from_external(
                entry_source,
                category_name=category_name,
                source="reference",
                source_lang=entry.get("source_lang"),
                target_lang=entry.get("target_lang"),
                languages=[{"lang_code": lang_code, "value": entry_target}],
            )
        except Exception:
            continue


def clear_glossary() -> int:
    _ensure_db()
    engine = get_engine()
    with engine.begin() as conn:
        res = conn.execute(text("DELETE FROM glossary"))
    return res.rowcount or 0


def delete_glossary(entry_id: int) -> int:
    _ensure_db()
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT source_text FROM glossary WHERE id = :id"),
            {"id": entry_id},
        ).fetchone()
        source_text = row[0] if row else None
        res = conn.execute(text("DELETE FROM glossary WHERE id = :id"), {"id": entry_id})

    if source_text:
        try:
            term_repo.delete_by_term(source_text)
        except Exception:
            pass

    return res.rowcount or 0


def batch_delete_glossary(ids: list[int]) -> int:
    if not ids:
        return 0
    _ensure_db()
    engine = get_engine()
    with engine.begin() as conn:
        res = conn.execute(text("DELETE FROM glossary WHERE id = ANY(:ids)"), {"ids": ids})
    return res.rowcount or 0
