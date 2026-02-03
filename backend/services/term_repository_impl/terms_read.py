from __future__ import annotations

import json

from .db import _connect, _ensure_db, _normalize_text
from .helpers import _fetch_aliases, _fetch_languages


def get_term(term_id: int) -> dict:
    _ensure_db()
    with _connect() as conn:
        term_row = conn.execute(
            (
                "SELECT t.*, c.name AS category_name "
                "FROM terms t "
                "LEFT JOIN categories c ON c.id = t.category_id "
                "WHERE t.id = ?"
            ),
            (term_id,),
        ).fetchone()
        if not term_row:
            raise ValueError("術語不存在")
        term = dict(term_row)
        term["languages"] = _fetch_languages(conn, term_id)
        term["aliases"] = _fetch_aliases(conn, term_id)
    return term


def list_versions(term_id: int) -> list[dict]:
    _ensure_db()
    with _connect() as conn:
        rows = conn.execute(
            (
                "SELECT id, term_id, diff, created_by, created_at "
                "FROM term_versions WHERE term_id = ? "
                "ORDER BY created_at DESC, id DESC"
            ),
            (term_id,),
        ).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        if item.get("diff"):
            try:
                item["diff"] = json.loads(item["diff"])
            except Exception:
                pass
        items.append(item)
    return items


def list_terms(filters: dict) -> list[dict]:  # noqa: C901
    _ensure_db()
    where = []
    params: list = []

    q = _normalize_text(filters.get("q"))
    if q:
        where.append(
            "(t.term_norm LIKE ? OR EXISTS ("
            "SELECT 1 FROM term_aliases a "
            "WHERE a.term_id = t.id AND a.alias_norm LIKE ?"
            "))"
        )
        like = f"%{q.lower()}%"
        params.extend([like, like])

    category_id = filters.get("category_id")
    if category_id:
        where.append("t.category_id = ?")
        params.append(category_id)

    status = filters.get("status")
    if status:
        where.append("t.status = ?")
        params.append(status)

    created_by = _normalize_text(filters.get("created_by"))
    if created_by:
        where.append("t.created_by = ?")
        params.append(created_by)

    source = _normalize_text(filters.get("source"))
    if source:
        where.append("t.source = ?")
        params.append(source)

    filename = _normalize_text(filters.get("filename"))
    if filename:
        where.append("t.filename LIKE ?")
        params.append(f"%{filename}%")

    date_from = filters.get("date_from")
    if date_from:
        where.append("t.created_at >= ?")
        params.append(date_from)

    date_to = filters.get("date_to")
    if date_to:
        where.append("t.created_at <= ?")
        params.append(date_to)

    missing_lang = filters.get("missing_lang")
    if missing_lang:
        where.append(
            "NOT EXISTS ("
            "SELECT 1 FROM term_languages tl "
            "WHERE tl.term_id = t.id AND tl.lang_code = ? "
            "AND tl.value IS NOT NULL AND tl.value != ''"
            ")"
        )
        params.append(missing_lang)

    has_alias = filters.get("has_alias")
    if has_alias is not None:
        if has_alias:
            where.append("EXISTS (SELECT 1 FROM term_aliases a WHERE a.term_id = t.id)")
        else:
            where.append("NOT EXISTS (SELECT 1 FROM term_aliases a WHERE a.term_id = t.id)")

    clause = " AND ".join(where) if where else "1=1"
    sql = (
        "SELECT t.*, c.name AS category_name "
        "FROM terms t "
        "LEFT JOIN categories c ON c.id = t.category_id "
        f"WHERE {clause} "
        "ORDER BY t.updated_at DESC, t.id DESC"
    )
    with _connect() as conn:
        rows = conn.execute(sql, params).fetchall()
        items = [dict(row) for row in rows]
        for item in items:
            term_id = item["id"]
            item["languages"] = _fetch_languages(conn, term_id)
            item["aliases"] = _fetch_aliases(conn, term_id)
    return items
