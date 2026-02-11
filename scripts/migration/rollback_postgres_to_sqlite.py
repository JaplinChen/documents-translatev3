from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from sqlalchemy import text

from backend.config import settings
from backend.db.engine import get_engine
from backend.services.translation_memory import DB_PATH, _ensure_db


SQLITE_DB = Path("data/translation_memory.db")

TABLES = [
    "tm_categories",
    "glossary",
    "tm",
    "term_feedback",
    "learning_events",
    "learning_stats",
]


def _fetch_postgres(table: str) -> list[dict]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(text(f"SELECT * FROM {table}")).fetchall()
    return [dict(row._mapping) for row in rows]


def _clear_sqlite(conn: sqlite3.Connection) -> None:
    for table in TABLES:
        conn.execute(f"DELETE FROM {table}")
    conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-clear", action="store_true", help="保留現有 SQLite 資料")
    args = parser.parse_args()

    if not (settings.database_url or "").startswith("postgresql"):
        raise SystemExit("DATABASE_URL 未設定或不是 PostgreSQL")

    _ensure_db()
    SQLITE_DB.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(SQLITE_DB) as sconn:
        if not args.no_clear:
            _clear_sqlite(sconn)

        for table in TABLES:
            rows = _fetch_postgres(table)
            if not rows:
                continue
            if table == "learning_events":
                for row in rows:
                    if "event_id" in row and "id" not in row:
                        row["id"] = row.pop("event_id")
            columns = list(rows[0].keys())
            placeholders = ",".join(["?"] * len(columns))
            insert_sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
            values = [tuple(row.get(col) for col in columns) for row in rows]
            sconn.executemany(insert_sql, values)
        sconn.commit()

    print("PostgreSQL -> SQLite 回滾完成")
    print("提醒：若要切回 SQLite，請移除或清空 DATABASE_URL")


if __name__ == "__main__":
    main()
