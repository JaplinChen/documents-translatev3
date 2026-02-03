from __future__ import annotations

from sqlalchemy import text

from backend.db.engine import get_engine

from .db import _ensure_db


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
        _ensure_db()
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO learning_events "
                    "(event_type, scope_type, scope_id, actor_type, entity_type, entity_id, "
                    "source_text, target_text, source_lang, target_lang, created_at) "
                    "VALUES (:event_type, :scope_type, :scope_id, :actor_type, :entity_type, :entity_id, "
                    ":source_text, :target_text, :source_lang, :target_lang, now())"
                ),
                {
                    "event_type": event_type,
                    "scope_type": scope_type,
                    "scope_id": scope_id,
                    "actor_type": "system",
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "source_text": source_text,
                    "target_text": target_text,
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                },
            )
    except Exception:
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
    params = {}
    if event_type:
        where.append("event_type = :event_type")
        params["event_type"] = event_type
    if entity_type:
        where.append("entity_type = :entity_type")
        params["entity_type"] = entity_type
    if scope_type:
        where.append("scope_type = :scope_type")
        params["scope_type"] = scope_type
    if scope_id:
        where.append("scope_id = :scope_id")
        params["scope_id"] = scope_id
    if source_lang:
        where.append("source_lang = :source_lang")
        params["source_lang"] = source_lang
    if target_lang:
        where.append("target_lang = :target_lang")
        params["target_lang"] = target_lang
    if q:
        where.append("(source_text ILIKE :q OR target_text ILIKE :q)")
        params["q"] = f"%{q}%"
    if date_from:
        where.append("created_at::date >= :date_from")
        params["date_from"] = date_from
    if date_to:
        where.append("created_at::date <= :date_to")
        params["date_to"] = date_to
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    sort_by = (sort_by or "id").lower()
    sort_dir = "ASC" if (sort_dir or "desc").lower() == "asc" else "DESC"
    if sort_by == "created_at":
        sort_column = "created_at"
    else:
        sort_column = "event_id"

    engine = get_engine()
    with engine.begin() as conn:
        total = conn.execute(
            text(f"SELECT COUNT(1) FROM learning_events {where_sql}"),
            params,
        ).fetchone()[0]
        rows = conn.execute(
            text(
                "SELECT event_id, event_type, scope_type, scope_id, entity_type, entity_id, "
                "source_text, target_text, source_lang, target_lang, created_at "
                f"FROM learning_events {where_sql} "
                f"ORDER BY {sort_column} {sort_dir} LIMIT :limit OFFSET :offset"
            ),
            {**params, "limit": limit, "offset": offset},
        ).fetchall()
    items = []
    for row in rows:
        data = dict(row._mapping)
        if "event_id" in data and "id" not in data:
            data["id"] = data.pop("event_id")
        items.append(data)
    return items, int(total or 0)


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
    params = {}
    if scope_type:
        where.append("scope_type = :scope_type")
        params["scope_type"] = scope_type
    if scope_id:
        where.append("scope_id = :scope_id")
        params["scope_id"] = scope_id
    if date_from:
        where.append("stat_date >= :date_from")
        params["date_from"] = date_from
    if date_to:
        where.append("stat_date <= :date_to")
        params["date_to"] = date_to
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    sort_by = (sort_by or "stat_date").lower()
    sort_dir = "ASC" if (sort_dir or "desc").lower() == "asc" else "DESC"
    if sort_by == "created_at":
        sort_column = "created_at"
    elif sort_by == "id":
        sort_column = "id"
    else:
        sort_column = "stat_date"

    engine = get_engine()
    with engine.begin() as conn:
        total = conn.execute(
            text(f"SELECT COUNT(1) FROM learning_stats {where_sql}"),
            params,
        ).fetchone()[0]
        rows = conn.execute(
            text(
                "SELECT id, stat_date, scope_type, scope_id, "
                "tm_hit_rate, glossary_hit_rate, overwrite_rate, "
                "auto_promotion_error_rate, wrong_suggestion_rate, created_at "
                f"FROM learning_stats {where_sql} "
                f"ORDER BY {sort_column} {sort_dir}, id DESC LIMIT :limit OFFSET :offset"
            ),
            {**params, "limit": limit, "offset": offset},
        ).fetchall()
    return [dict(row._mapping) for row in rows], int(total or 0)
