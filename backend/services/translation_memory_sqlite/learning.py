from __future__ import annotations

import sqlite3

from .db import DB_PATH, _ensure_db


def _record_learning_event(
    event_type: str,
    source_text: str | None = None,
    target_text: str | None = None,
    source_lang: str | None = None,
    target_lang: str | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    scope_type: str = "project",
    scope_id: str | None = "default",
) -> None:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                (
                    "INSERT INTO learning_events "
                    "(event_type, scope_type, scope_id, entity_type, entity_id, "
                    "source_text, target_text, source_lang, target_lang) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
                ),
                (
                    event_type,
                    scope_type,
                    scope_id,
                    entity_type,
                    entity_id,
                    source_text,
                    target_text,
                    source_lang,
                    target_lang,
                ),
            )
            conn.commit()
    except Exception:
        # 避免影響主流程
        return


def list_learning_events(
    limit: int = 200,
    offset: int = 0,
    event_type: str | None = None,
    entity_type: str | None = None,
    scope_type: str | None = None,
    scope_id: str | None = None,
    source_lang: str | None = None,
    target_lang: str | None = None,
    q: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sort_by: str | None = None,
    sort_dir: str | None = None,
) -> tuple[list[dict], int]:
    _ensure_db()
    limit = max(1, min(int(limit or 200), 1000))
    offset = max(0, int(offset or 0))
    where = []
    params = []
    if event_type:
        where.append("event_type = ?")
        params.append(event_type)
    if entity_type:
        where.append("entity_type = ?")
        params.append(entity_type)
    if scope_type:
        where.append("scope_type = ?")
        params.append(scope_type)
    if scope_id:
        where.append("scope_id = ?")
        params.append(scope_id)
    if source_lang:
        where.append("source_lang = ?")
        params.append(source_lang)
    if target_lang:
        where.append("target_lang = ?")
        params.append(target_lang)
    if q:
        where.append("(source_text LIKE ? OR target_text LIKE ?)")
        like_q = f"%{q}%"
        params.extend([like_q, like_q])
    if date_from:
        where.append("date(created_at) >= date(?)")
        params.append(date_from)
    if date_to:
        where.append("date(created_at) <= date(?)")
        params.append(date_to)
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    sort_by = (sort_by or "id").lower()
    sort_dir = "ASC" if (sort_dir or "desc").lower() == "asc" else "DESC"
    sort_column = "created_at" if sort_by == "created_at" else "id"

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            f"SELECT COUNT(1) as cnt FROM learning_events {where_sql}",
            params,
        )
        total = int(cur.fetchone()["cnt"] or 0)
        cur = conn.execute(
            (
                "SELECT id, event_type, scope_type, scope_id, entity_type, entity_id, "
                "source_text, target_text, source_lang, target_lang, created_at "
                f"FROM learning_events {where_sql} "
                f"ORDER BY {sort_column} {sort_dir} LIMIT ? OFFSET ?"
            ),
            [*params, limit, offset],
        )
        items = [dict(row) for row in cur.fetchall()]
    return items, total


def list_learning_stats(
    limit: int = 30,
    offset: int = 0,
    scope_type: str | None = None,
    scope_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sort_by: str | None = None,
    sort_dir: str | None = None,
) -> tuple[list[dict], int]:
    _ensure_db()
    limit = max(1, min(int(limit or 30), 365))
    offset = max(0, int(offset or 0))
    where = []
    params = []
    if scope_type:
        where.append("scope_type = ?")
        params.append(scope_type)
    if scope_id:
        where.append("scope_id = ?")
        params.append(scope_id)
    if date_from:
        where.append("date(stat_date) >= date(?)")
        params.append(date_from)
    if date_to:
        where.append("date(stat_date) <= date(?)")
        params.append(date_to)
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    sort_by = (sort_by or "stat_date").lower()
    sort_dir = "ASC" if (sort_dir or "desc").lower() == "asc" else "DESC"
    if sort_by == "created_at":
        sort_column = "created_at"
    elif sort_by == "id":
        sort_column = "id"
    else:
        sort_column = "stat_date"

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            f"SELECT COUNT(1) as cnt FROM learning_stats {where_sql}",
            params,
        )
        total = int(cur.fetchone()["cnt"] or 0)
        cur = conn.execute(
            (
                "SELECT id, stat_date, scope_type, scope_id, "
                "tm_hit_rate, glossary_hit_rate, overwrite_rate, "
                "auto_promotion_error_rate, wrong_suggestion_rate, created_at "
                f"FROM learning_stats {where_sql} "
                f"ORDER BY {sort_column} {sort_dir}, id DESC LIMIT ? OFFSET ?"
            ),
            [*params, limit, offset],
        )
        items = [dict(row) for row in cur.fetchall()]
    return items, total
