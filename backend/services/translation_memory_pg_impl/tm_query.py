from __future__ import annotations

from sqlalchemy import text

from backend.db.engine import get_engine

from .db import _ensure_db


def get_tm(limit: int = 200) -> list[dict]:
    _ensure_db()
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT t.id, t.source_lang, t.target_lang, t.source_text, "
                "t.target_text, t.category_id, c.name as category_name, "
                "t.domain, t.category, t.scope_type, t.scope_id, t.status, "
                "t.hit_count, t.overwrite_count, t.last_hit_at, t.created_at "
                "FROM tm t LEFT JOIN tm_categories c ON t.category_id = c.id "
                "WHERE NOT EXISTS ("
                "  SELECT 1 FROM glossary g "
                "  WHERE g.source_text = t.source_text "
                "  AND g.source_lang = t.source_lang "
                "  AND g.target_lang = t.target_lang"
                ") "
                "ORDER BY t.id DESC LIMIT :limit"
            ),
            {"limit": limit},
        ).fetchall()
    return [
        {
            "id": row[0],
            "source_lang": row[1],
            "target_lang": row[2],
            "source_text": row[3],
            "target_text": row[4],
            "category_id": row[5],
            "category_name": row[6],
            "domain": row[7],
            "category": row[8],
            "scope_type": row[9],
            "scope_id": row[10],
            "status": row[11],
            "hit_count": row[12],
            "overwrite_count": row[13],
            "last_hit_at": row[14],
            "created_at": row[15],
        }
        for row in rows
    ]


def get_tm_count() -> int:
    _ensure_db()
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                "SELECT COUNT(1) FROM tm t "
                "WHERE NOT EXISTS ("
                "  SELECT 1 FROM glossary g "
                "  WHERE g.source_text = t.source_text "
                "  AND g.source_lang = t.source_lang "
                "  AND g.target_lang = t.target_lang"
                ")"
            )
        ).fetchone()
    return int(row[0] or 0)


def get_tm_terms(
    source_lang: str,
    target_lang: str,
    limit: int = 200,
) -> list[tuple[str, str]]:
    _ensure_db()
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT source_text, target_text FROM tm "
                "WHERE source_lang = :source_lang AND target_lang = :target_lang "
                "ORDER BY id DESC LIMIT :limit"
            ),
            {"source_lang": source_lang, "target_lang": target_lang, "limit": limit},
        ).fetchall()
    return [(row[0], row[1]) for row in rows]


def get_tm_terms_any(
    target_lang: str,
    limit: int = 200,
) -> list[tuple[str, str]]:
    _ensure_db()
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT source_text, target_text FROM tm "
                "WHERE target_lang = :target_lang "
                "ORDER BY id DESC LIMIT :limit"
            ),
            {"target_lang": target_lang, "limit": limit},
        ).fetchall()
    return [(row[0], row[1]) for row in rows]
