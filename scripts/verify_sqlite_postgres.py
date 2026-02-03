from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from sqlalchemy import text

from backend.config import settings
from backend.db.engine import get_engine
from backend.services.translation_memory import _ensure_db as ensure_sqlite_db


SQLITE_DB = Path("data/translation_memory.db")

TABLES = {
    "tm_categories": {
        "sqlite": ["id", "name", "sort_order"],
        "postgres": ["id", "name", "sort_order"],
        "checksum": ["name", "sort_order"],
    },
    "glossary": {
        "sqlite": [
            "id",
            "source_lang",
            "target_lang",
            "source_text",
            "target_text",
            "priority",
            "category_id",
            "domain",
            "category",
            "scope_type",
            "scope_id",
            "status",
            "hit_count",
            "overwrite_count",
            "last_hit_at",
            "created_at",
        ],
        "postgres": [
            "id",
            "source_lang",
            "target_lang",
            "source_text",
            "target_text",
            "priority",
            "category_id",
            "domain",
            "category",
            "scope_type",
            "scope_id",
            "status",
            "hit_count",
            "overwrite_count",
            "last_hit_at",
            "created_at",
        ],
        "checksum": [
            "source_lang",
            "target_lang",
            "source_text",
            "target_text",
            "priority",
            "category_id",
            "domain",
            "category",
            "scope_type",
            "scope_id",
            "status",
            "hit_count",
            "overwrite_count",
        ],
    },
    "tm": {
        "sqlite": [
            "id",
            "source_lang",
            "target_lang",
            "source_text",
            "target_text",
            "category_id",
            "domain",
            "category",
            "scope_type",
            "scope_id",
            "status",
            "hit_count",
            "overwrite_count",
            "last_hit_at",
            "hash",
            "created_at",
        ],
        "postgres": [
            "id",
            "source_lang",
            "target_lang",
            "source_text",
            "target_text",
            "category_id",
            "domain",
            "category",
            "scope_type",
            "scope_id",
            "status",
            "hit_count",
            "overwrite_count",
            "last_hit_at",
            "hash",
            "created_at",
        ],
        "checksum": [
            "source_lang",
            "target_lang",
            "source_text",
            "target_text",
            "category_id",
            "domain",
            "category",
            "scope_type",
            "scope_id",
            "status",
            "hit_count",
            "overwrite_count",
            "hash",
        ],
    },
    "term_feedback": {
        "sqlite": [
            "id",
            "source_text",
            "target_text",
            "source_lang",
            "target_lang",
            "correction_count",
            "last_corrected_at",
        ],
        "postgres": [
            "id",
            "source_text",
            "target_text",
            "source_lang",
            "target_lang",
            "correction_count",
            "last_corrected_at",
        ],
        "checksum": [
            "source_text",
            "target_text",
            "source_lang",
            "target_lang",
            "correction_count",
        ],
    },
    "learning_events": {
        "sqlite": [
            "id",
            "event_type",
            "scope_type",
            "scope_id",
            "entity_type",
            "entity_id",
            "source_text",
            "target_text",
            "source_lang",
            "target_lang",
            "created_at",
        ],
        "postgres": [
            "event_id",
            "event_type",
            "scope_type",
            "scope_id",
            "entity_type",
            "entity_id",
            "source_text",
            "target_text",
            "source_lang",
            "target_lang",
            "created_at",
        ],
        "checksum": [
            "event_type",
            "scope_type",
            "scope_id",
            "entity_type",
            "entity_id",
            "source_text",
            "target_text",
            "source_lang",
            "target_lang",
        ],
    },
    "learning_stats": {
        "sqlite": [
            "id",
            "stat_date",
            "scope_type",
            "scope_id",
            "tm_hit_rate",
            "glossary_hit_rate",
            "overwrite_rate",
            "auto_promotion_error_rate",
            "wrong_suggestion_rate",
            "created_at",
        ],
        "postgres": [
            "id",
            "stat_date",
            "scope_type",
            "scope_id",
            "tm_hit_rate",
            "glossary_hit_rate",
            "overwrite_rate",
            "auto_promotion_error_rate",
            "wrong_suggestion_rate",
            "created_at",
        ],
        "checksum": [
            "stat_date",
            "scope_type",
            "scope_id",
            "tm_hit_rate",
            "glossary_hit_rate",
            "overwrite_rate",
            "auto_promotion_error_rate",
            "wrong_suggestion_rate",
        ],
    },
}


def _normalize_value(value):
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "as_tuple") and hasattr(value, "quantize"):
        try:
            return round(float(value), 4)
        except Exception:
            return str(value)
    if isinstance(value, float):
        return round(value, 4)
    return value


def _checksum(rows: list[tuple]) -> str:
    md5 = hashlib.md5()
    for row in rows:
        norm = tuple(_normalize_value(v) for v in row)
        md5.update(repr(norm).encode("utf-8"))
    return md5.hexdigest()


def _fetch_sqlite(table: str, cols: list[str]) -> list[tuple]:
    if not SQLITE_DB.exists():
        return []
    with sqlite3.connect(SQLITE_DB) as conn:
        cur = conn.execute(
            f"SELECT {', '.join(cols)} FROM {table} ORDER BY {cols[0]} ASC"
        )
        return cur.fetchall()


def _fetch_postgres(table: str, cols: list[str]) -> list[tuple]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                f"SELECT {', '.join(cols)} FROM {table} ORDER BY {cols[0]} ASC"
            )
        ).fetchall()
    return [tuple(row) for row in rows]


def main() -> None:
    if not SQLITE_DB.exists():
        raise SystemExit("找不到 data/translation_memory.db")
    if not (settings.database_url or "").startswith("postgresql"):
        raise SystemExit("DATABASE_URL 未設定或不是 PostgreSQL")

    ensure_sqlite_db()

    ok = True
    for table, meta in TABLES.items():
        s_cols = meta["sqlite"]
        p_cols = meta["postgres"]
        c_cols = meta["checksum"]
        s_rows = _fetch_sqlite(table, s_cols)
        p_rows = _fetch_postgres(table, p_cols)
        s_cnt = len(s_rows)
        p_cnt = len(p_rows)
        s_idx = [s_cols.index(c) for c in c_cols]
        p_idx = [p_cols.index(c) for c in c_cols]
        s_sum = _checksum([tuple(r[i] for i in s_idx) for r in s_rows])
        p_sum = _checksum([tuple(r[i] for i in p_idx) for r in p_rows])
        match = s_cnt == p_cnt and s_sum == p_sum
        status = "OK" if match else "MISMATCH"
        print(f"{table}: sqlite={s_cnt} postgres={p_cnt} checksum={status}")
        if not match:
            ok = False
    if not ok:
        raise SystemExit("資料一致性檢查失敗")
    print("資料一致性檢查通過")


if __name__ == "__main__":
    main()
