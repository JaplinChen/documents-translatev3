from __future__ import annotations

import sqlite3
from pathlib import Path

from .db import DB_PATH, _ensure_db


def list_tm_categories() -> list[dict]:
    _ensure_db()
    # 1. Proactively sync names from terms.db to tm_categories for UI consistency
    terms_db = Path("data/terms.db")
    if terms_db.exists():
        try:
            with sqlite3.connect(terms_db) as tconn:
                tconn.row_factory = sqlite3.Row
                t_rows = tconn.execute("SELECT name, sort_order FROM categories").fetchall()
                t_names = {r["name"] for r in t_rows}
                t_data = {r["name"]: r["sort_order"] for r in t_rows}

            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                c_rows = conn.execute("SELECT name FROM tm_categories").fetchall()
                c_names = {r["name"] for r in c_rows}

                missing = t_names - c_names
                if missing:
                    for name in missing:
                        conn.execute(
                            "INSERT OR IGNORE INTO tm_categories (name, sort_order) VALUES (?, ?)",
                            (name, t_data[name]),
                        )
                    conn.commit()
        except Exception as e:
            print(f"Error syncing categories in list_tm_categories: {e}")

    # 2. Return the merged list with accurate counts
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        # Get counts from glossary and tm tables in translation_memory.db
        query = """
            SELECT 
                c.id, 
                c.name, 
                c.sort_order,
                (SELECT COUNT(*) FROM glossary g WHERE g.category_id = c.id) as glossary_count,
                (SELECT COUNT(*) FROM tm t WHERE t.category_id = c.id) as tm_count
            FROM tm_categories c
            ORDER BY c.sort_order, c.id
        """
        rows = conn.execute(query).fetchall()
        result = [dict(row) for row in rows]

    # 3. Augment with term_count from terms.db if possible
    if terms_db.exists():
        try:
            with sqlite3.connect(terms_db) as tconn:
                tconn.row_factory = sqlite3.Row
                for item in result:
                    trow = tconn.execute(
                        "SELECT COUNT(*) as cnt FROM terms t JOIN categories c ON t.category_id = c.id WHERE c.name = ?",
                        (item["name"],),
                    ).fetchone()
                    # Add unified terms count to the item
                    item["unified_term_count"] = trow["cnt"] if trow else 0
        except Exception:
            pass

    return result


def create_tm_category(name: str, sort_order: int | None = None) -> dict:
    _ensure_db()
    name = name.strip()
    if not name:
        raise ValueError("分類名稱不可為空")
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "INSERT INTO tm_categories (name, sort_order) VALUES (?, ?)",
            (name, sort_order or 0),
        )
        conn.commit()

        # Sync to terms.db if exists
        terms_db = Path("data/terms.db")
        if terms_db.exists():
            try:
                with sqlite3.connect(terms_db) as tconn:
                    tconn.execute(
                        "INSERT OR IGNORE INTO categories (name, sort_order) VALUES (?, ?)",
                        (name, sort_order or 0),
                    )
                    tconn.commit()
            except Exception as e:
                print(f"Error syncing create to terms.db: {e}")

        return {"id": cur.lastrowid, "name": name, "sort_order": sort_order or 0}


def update_tm_category(category_id: int, name: str, sort_order: int | None = None) -> dict:
    _ensure_db()
    name = name.strip()
    if not name:
        raise ValueError("分類名稱不可為空")
    with sqlite3.connect(DB_PATH) as conn:
        # Get old name for syncing
        old_row = conn.execute(
            "SELECT name FROM tm_categories WHERE id = ?", (category_id,)
        ).fetchone()
        old_name = old_row[0] if old_row else None

        conn.execute(
            "UPDATE tm_categories SET name = ?, sort_order = ? WHERE id = ?",
            (name, sort_order or 0, category_id),
        )

        if old_name and old_name != name:
            # Sync to preserve_terms in same DB
            conn.execute(
                "UPDATE preserve_terms SET category = ? WHERE category = ?", (name, old_name)
            )

            # Sync to terms.db if exists
            terms_db = Path("data/terms.db")
            if terms_db.exists():
                try:
                    with sqlite3.connect(terms_db) as tconn:
                        tconn.execute(
                            "UPDATE categories SET name = ? WHERE name = ?", (name, old_name)
                        )
                        tconn.commit()
                except Exception as e:
                    print(f"Error syncing to terms.db: {e}")

        conn.commit()
        return {"id": category_id, "name": name, "sort_order": sort_order or 0}


def delete_tm_category(category_id: int) -> None:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        # Get name for syncing
        row = conn.execute("SELECT name FROM tm_categories WHERE id = ?", (category_id,)).fetchone()
        name = row[0] if row else None

        # Update items to NULL
        conn.execute("UPDATE glossary SET category_id = NULL WHERE category_id = ?", (category_id,))
        conn.execute("UPDATE tm SET category_id = NULL WHERE category_id = ?", (category_id,))

        if name:
            # Sync to preserve_terms: set back to '未分類' string
            conn.execute(
                "UPDATE preserve_terms SET category = '未分類' WHERE category = ?", (name,)
            )

            # Sync to terms.db Categories table
            terms_db = Path("data/terms.db")
            if terms_db.exists():
                try:
                    with sqlite3.connect(terms_db) as tconn:
                        # Find the corresponding category in terms.db by name
                        trow = tconn.execute(
                            "SELECT id FROM categories WHERE name = ?", (name,)
                        ).fetchone()
                        if trow:
                            tid = trow[0]
                            # Update terms in terms.db to NULL
                            tconn.execute(
                                "UPDATE terms SET category_id = NULL WHERE category_id = ?", (tid,)
                            )
                            tconn.execute("DELETE FROM categories WHERE id = ?", (tid,))
                            tconn.commit()
                except Exception as e:
                    print(f"Error syncing delete to terms.db: {e}")

        conn.execute("DELETE FROM tm_categories WHERE id = ?", (category_id,))
        conn.commit()
