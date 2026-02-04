from __future__ import annotations

from .categories import _get_or_create_category
from .db import _connect, _ensure_db, _normalize_text
from .helpers import _fetch_term_full, _record_version, _replace_aliases, _upsert_languages
from .terms_read import get_term
from .validation import _check_alias_conflict, _check_term_duplicate


def _get_category_name_by_id(category_id: int | None) -> str | None:
    if not category_id:
        return None
    _ensure_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT name FROM categories WHERE id = ?",
            (category_id,),
        ).fetchone()
    return row["name"] if row else None


def _resolve_tm_category_id(category_name: str | None) -> int | None:
    if not category_name:
        return None
    try:
        from backend.services.translation_memory_adapter import list_tm_categories
    except Exception:
        return None
    try:
        items = list_tm_categories()
    except Exception:
        return None
    for item in items or []:
        if (item.get("name") or "").strip() == category_name:
            return item.get("id")
    return None


def _pick_target_text(payload: dict) -> str:
    languages = payload.get("languages") or []
    target_lang = payload.get("target_lang")
    if target_lang:
        for lang in languages:
            if lang.get("lang_code") == target_lang and lang.get("value"):
                return lang.get("value")
    for lang in languages:
        if lang.get("value"):
            return lang.get("value")
    return ""


def _sync_reference_to_glossary(payload: dict, term_text: str) -> None:
    try:
        from backend.services.translation_memory_adapter import upsert_glossary
    except Exception:
        return
    category_name = payload.get("category_name") or _get_category_name_by_id(payload.get("category_id"))
    category_id = _resolve_tm_category_id(category_name)
    entry = {
        "source_lang": payload.get("source_lang") or "vi",
        "target_lang": payload.get("target_lang") or "zh-TW",
        "source_text": term_text,
        "target_text": _pick_target_text(payload),
        "priority": payload.get("priority") or 0,
        "category_id": category_id,
    }
    upsert_glossary(entry)


def create_term(payload: dict) -> dict:
    _ensure_db()
    term = _normalize_text(payload.get("term"))
    if not term:
        raise ValueError("術語不可為空")
    term_norm = term.lower()
    _check_term_duplicate(term_norm)

    aliases = payload.get("aliases") or []
    alias_norms = [_normalize_text(a).lower() for a in aliases if _normalize_text(a)]
    _check_alias_conflict(alias_norms)

    category_id = _get_or_create_category(
        payload.get("category_id"),
        payload.get("category_name"),
        allow_create=payload.get("allow_create_category", True),
    )
    status = payload.get("status") or "active"
    case_rule = payload.get("case_rule")
    note = payload.get("note")
    created_by = payload.get("created_by")

    with _connect() as conn:
        cur = conn.execute(
            (
                "INSERT INTO terms "
                "(term, term_norm, category_id, status, target_lang, case_rule, note, source, source_lang, priority, filename, created_by) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            ),
            (
                term,
                term_norm,
                category_id,
                status,
                payload.get("target_lang"),
                case_rule,
                note,
                payload.get("source"),
                payload.get("source_lang"),
                payload.get("priority") or 0,
                payload.get("filename"),
                created_by,
            ),
        )
        term_id = cur.lastrowid
        _upsert_languages(conn, term_id, payload.get("languages") or [])
        _replace_aliases(conn, term_id, aliases)
        after = _fetch_term_full(conn, term_id)
        _record_version(conn, term_id, before=None, after=after, created_by=created_by)
    if payload.get("source") == "reference" and not payload.get("_from_external"):
        _sync_reference_to_glossary(payload, term)
    return get_term(term_id)


def update_term(term_id: int, payload: dict) -> dict:
    _ensure_db()
    term = _normalize_text(payload.get("term"))
    if not term:
        raise ValueError("術語不可為空")
    term_norm = term.lower()
    _check_term_duplicate(term_norm, exclude_id=term_id)

    aliases = payload.get("aliases") or []
    alias_norms = [_normalize_text(a).lower() for a in aliases if _normalize_text(a)]
    _check_alias_conflict(alias_norms, exclude_term_id=term_id)

    category_id = _get_or_create_category(
        payload.get("category_id"),
        payload.get("category_name"),
        allow_create=payload.get("allow_create_category", True),
    )
    status = payload.get("status") or "active"
    case_rule = payload.get("case_rule")
    note = payload.get("note")

    with _connect() as conn:
        before = _fetch_term_full(conn, term_id)
        conn.execute(
            (
                "UPDATE terms SET term = ?, term_norm = ?, category_id = ?, "
                "status = ?, target_lang = ?, case_rule = ?, note = ?, source = ?, source_lang = ?, "
                "priority = ?, filename = ?, "
                "updated_at = CURRENT_TIMESTAMP "
                "WHERE id = ?"
            ),
            (
                term,
                term_norm,
                category_id,
                status,
                payload.get("target_lang"),
                case_rule,
                note,
                payload.get("source"),
                payload.get("source_lang"),
                payload.get("priority") or 0,
                payload.get("filename"),
                term_id,
            ),
        )
        _upsert_languages(conn, term_id, payload.get("languages") or [])
        _replace_aliases(conn, term_id, aliases)
        after = _fetch_term_full(conn, term_id)
        _record_version(
            conn,
            term_id,
            before=before,
            after=after,
            created_by=payload.get("created_by"),
        )
    if payload.get("source") == "reference" and not payload.get("_from_external"):
        _sync_reference_to_glossary(payload, term)
    return get_term(term_id)


def delete_term(term_id: int) -> None:
    _ensure_db()
    with _connect() as conn:
        before = _fetch_term_full(conn, term_id)
        conn.execute("DELETE FROM term_languages WHERE term_id = ?", (term_id,))
        conn.execute("DELETE FROM term_aliases WHERE term_id = ?", (term_id,))
        conn.execute("DELETE FROM terms WHERE id = ?", (term_id,))
        _record_version(conn, term_id, before=before, after=None, created_by=None)
