from __future__ import annotations

from .db import _connect, _ensure_db, _normalize_text


def _sync_tm_categories() -> None:
    try:
        from backend.services.translation_memory_pg_impl.categories import list_tm_categories
    except Exception:
        return

    try:
        tm_categories = list_tm_categories()
    except Exception:
        return

    if not tm_categories:
        return

    _ensure_db()
    with _connect() as conn:
        for cat in tm_categories:
            name = _normalize_text(cat.get("name"))
            if not name:
                continue
            sort_order = int(cat.get("sort_order") or 0)
            row = conn.execute(
                "SELECT id, sort_order FROM categories WHERE name = ?",
                (name,),
            ).fetchone()
            if row:
                existing_sort = int(row["sort_order"] or 0)
                if existing_sort != sort_order:
                    conn.execute(
                        "UPDATE categories SET sort_order = ? WHERE id = ?",
                        (sort_order, row["id"]),
                    )
                continue
            conn.execute(
                "INSERT INTO categories (name, sort_order) VALUES (?, ?)",
                (name, sort_order),
            )
        conn.commit()


def list_categories() -> list[dict]:
    _sync_tm_categories()
    _ensure_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, name, sort_order FROM categories ORDER BY sort_order, id"
        ).fetchall()
    return [dict(row) for row in rows]


def get_category_id_by_name(name: str) -> int | None:
    _ensure_db()
    normalized = _normalize_text(name)
    if not normalized:
        return None
    with _connect() as conn:
        row = conn.execute(
            "SELECT id FROM categories WHERE name = ?",
            (normalized,),
        ).fetchone()
    return int(row["id"]) if row else None


def create_category(name: str, sort_order: int | None = None) -> dict:
    _ensure_db()
    name = _normalize_text(name)
    if not name:
        raise ValueError("分類名稱不可為空")
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO categories (name, sort_order) VALUES (?, ?)",
            (name, sort_order or 0),
        )
        conn.commit()
        return {"id": cur.lastrowid, "name": name, "sort_order": sort_order or 0}


def update_category(category_id: int, name: str, sort_order: int | None = None) -> dict:
    _ensure_db()
    name = _normalize_text(name)
    if not name:
        raise ValueError("分類名稱不可為空")
    with _connect() as conn:
        conn.execute(
            "UPDATE categories SET name = ?, sort_order = ? WHERE id = ?",
            (name, sort_order or 0, category_id),
        )
        conn.commit()
        return {"id": category_id, "name": name, "sort_order": sort_order or 0}


def delete_category(category_id: int) -> None:
    _ensure_db()
    with _connect() as conn:
        conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()


def _get_or_create_category(
    category_id: int | None,
    category_name: str | None,
    allow_create: bool = True,
) -> int | None:
    if category_id:
        return category_id
    if not category_name:
        return None
    normalized = _normalize_text(category_name)
    with _connect() as conn:
        row = conn.execute(
            "SELECT id FROM categories WHERE name = ?",
            (normalized,),
        ).fetchone()
        if row:
            return int(row["id"])
        if not allow_create:
            raise ValueError("分類不存在")
        cur = conn.execute(
            "INSERT INTO categories (name, sort_order) VALUES (?, 0)",
            (normalized,),
        )
        return cur.lastrowid
