from __future__ import annotations

from .categories import _get_or_create_category
from .db import _connect, _ensure_db, _normalize_text
from .helpers import _fetch_term_full, _record_version, _replace_aliases, _upsert_languages
from .terms_read import get_term
from .validation import _check_alias_conflict, _check_term_duplicate


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
    return get_term(term_id)


def delete_term(term_id: int) -> None:
    _ensure_db()
    with _connect() as conn:
        before = _fetch_term_full(conn, term_id)
        conn.execute("DELETE FROM term_languages WHERE term_id = ?", (term_id,))
        conn.execute("DELETE FROM term_aliases WHERE term_id = ?", (term_id,))
        conn.execute("DELETE FROM terms WHERE id = ?", (term_id,))
        _record_version(conn, term_id, before=before, after=None, created_by=None)
