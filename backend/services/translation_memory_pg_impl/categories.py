from __future__ import annotations

from sqlalchemy import text

from backend.db.engine import get_engine

from .db import _ensure_db


def list_tm_categories() -> list[dict]:
    _ensure_db()
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT c.id, c.name, c.sort_order, "
                "(SELECT COUNT(*) FROM glossary g WHERE g.category_id = c.id) as glossary_count, "
                "(SELECT COUNT(*) FROM tm t WHERE t.category_id = c.id) as tm_count "
                "FROM tm_categories c ORDER BY c.sort_order, c.id"
            )
        ).fetchall()
    return [dict(row._mapping) for row in rows]


def create_tm_category(name: str, sort_order: int | None = None) -> dict:
    _ensure_db()
    name = name.strip()
    if not name:
        raise ValueError("分類名稱不可為空")
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                "INSERT INTO tm_categories (name, sort_order) "
                "VALUES (:name, :sort_order) RETURNING id"
            ),
            {"name": name, "sort_order": sort_order or 0},
        ).fetchone()
        category_id = row[0] if row else None
    return {"id": category_id, "name": name, "sort_order": sort_order or 0}


def update_tm_category(category_id: int, name: str, sort_order: int | None = None) -> dict:
    _ensure_db()
    name = name.strip()
    if not name:
        raise ValueError("分類名稱不可為空")
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE tm_categories SET name = :name, sort_order = :sort_order WHERE id = :id"),
            {"name": name, "sort_order": sort_order or 0, "id": category_id},
        )
    return {"id": category_id, "name": name, "sort_order": sort_order or 0}


def delete_tm_category(category_id: int) -> None:
    _ensure_db()
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE glossary SET category_id = NULL WHERE category_id = :id"),
            {"id": category_id},
        )
        conn.execute(
            text("UPDATE tm SET category_id = NULL WHERE category_id = :id"),
            {"id": category_id},
        )
        conn.execute(text("DELETE FROM tm_categories WHERE id = :id"), {"id": category_id})
