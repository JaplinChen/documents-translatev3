from __future__ import annotations

import sqlite3
from pathlib import Path

from sqlalchemy import text

from backend.config import settings
from backend.db.engine import get_engine
from backend.db.models import Base


SQLITE_DB = Path("data/translation_memory.db")


def _fetch_all(conn: sqlite3.Connection, table: str) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    cur = conn.execute(f"SELECT * FROM {table}")
    return cur.fetchall()


def main() -> None:
    if not SQLITE_DB.exists():
        raise SystemExit("找不到 data/translation_memory.db")
    if not (settings.database_url or "").startswith("postgresql"):
        raise SystemExit("DATABASE_URL 未設定或不是 PostgreSQL")

    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    with sqlite3.connect(SQLITE_DB) as sconn, engine.begin() as pconn:
        # tm_categories
        for row in _fetch_all(sconn, "tm_categories"):
            pconn.execute(
                text(
                    "INSERT INTO tm_categories (id, name, sort_order) "
                    "VALUES (:id, :name, :sort_order) "
                    "ON CONFLICT (name) DO UPDATE SET sort_order = EXCLUDED.sort_order"
                ),
                dict(row),
            )

        # glossary
        for row in _fetch_all(sconn, "glossary"):
            pconn.execute(
                text(
                    "INSERT INTO glossary "
                    "(id, source_lang, target_lang, source_text, target_text, priority, "
                    "category_id, domain, category, scope_type, scope_id, status, "
                    "hit_count, overwrite_count, last_hit_at, created_at) "
                    "VALUES (:id, :source_lang, :target_lang, :source_text, :target_text, :priority, "
                    ":category_id, :domain, :category, :scope_type, :scope_id, :status, "
                    ":hit_count, :overwrite_count, :last_hit_at, :created_at) "
                    "ON CONFLICT (source_lang, target_lang, source_text) DO UPDATE SET "
                    "target_text = EXCLUDED.target_text, priority = EXCLUDED.priority, "
                    "category_id = EXCLUDED.category_id, domain = EXCLUDED.domain, "
                    "category = EXCLUDED.category, scope_type = EXCLUDED.scope_type, "
                    "scope_id = EXCLUDED.scope_id, status = EXCLUDED.status, "
                    "hit_count = EXCLUDED.hit_count, overwrite_count = EXCLUDED.overwrite_count, "
                    "last_hit_at = EXCLUDED.last_hit_at, created_at = EXCLUDED.created_at"
                ),
                dict(row),
            )

        # tm
        for row in _fetch_all(sconn, "tm"):
            pconn.execute(
                text(
                    "INSERT INTO tm "
                    "(id, source_lang, target_lang, source_text, target_text, category_id, "
                    "domain, category, scope_type, scope_id, status, hit_count, "
                    "overwrite_count, last_hit_at, hash, created_at) "
                    "VALUES (:id, :source_lang, :target_lang, :source_text, :target_text, :category_id, "
                    ":domain, :category, :scope_type, :scope_id, :status, :hit_count, "
                    ":overwrite_count, :last_hit_at, :hash, :created_at) "
                    "ON CONFLICT (hash) DO UPDATE SET "
                    "target_text = EXCLUDED.target_text, category_id = EXCLUDED.category_id, "
                    "domain = EXCLUDED.domain, category = EXCLUDED.category, "
                    "scope_type = EXCLUDED.scope_type, scope_id = EXCLUDED.scope_id, "
                    "status = EXCLUDED.status, hit_count = EXCLUDED.hit_count, "
                    "overwrite_count = EXCLUDED.overwrite_count, last_hit_at = EXCLUDED.last_hit_at"
                ),
                dict(row),
            )

        # term_feedback
        for row in _fetch_all(sconn, "term_feedback"):
            pconn.execute(
                text(
                    "INSERT INTO term_feedback "
                    "(id, source_text, target_text, source_lang, target_lang, correction_count, last_corrected_at) "
                    "VALUES (:id, :source_text, :target_text, :source_lang, :target_lang, "
                    ":correction_count, :last_corrected_at) "
                    "ON CONFLICT (source_text, target_text, source_lang, target_lang) DO UPDATE SET "
                    "correction_count = EXCLUDED.correction_count, "
                    "last_corrected_at = EXCLUDED.last_corrected_at"
                ),
                dict(row),
            )

        # learning_events
        for row in _fetch_all(sconn, "learning_events"):
            payload = dict(row)
            payload["event_id"] = payload.get("id")
            pconn.execute(
                text(
                    "INSERT INTO learning_events "
                    "(event_id, event_type, scope_type, scope_id, actor_type, entity_type, entity_id, "
                    "source_text, target_text, source_lang, target_lang, created_at) "
                    "VALUES (:event_id, :event_type, :scope_type, :scope_id, :actor_type, :entity_type, :entity_id, "
                    ":source_text, :target_text, :source_lang, :target_lang, :created_at) "
                    "ON CONFLICT (event_id) DO NOTHING"
                ),
                {
                    **payload,
                    "actor_type": "system",
                },
            )

        # learning_stats
        for row in _fetch_all(sconn, "learning_stats"):
            pconn.execute(
                text(
                    "INSERT INTO learning_stats "
                    "(id, stat_date, scope_type, scope_id, tm_hit_rate, glossary_hit_rate, "
                    "overwrite_rate, auto_promotion_error_rate, wrong_suggestion_rate, created_at) "
                    "VALUES (:id, :stat_date, :scope_type, :scope_id, :tm_hit_rate, :glossary_hit_rate, "
                    ":overwrite_rate, :auto_promotion_error_rate, :wrong_suggestion_rate, :created_at) "
                    "ON CONFLICT (id) DO NOTHING"
                ),
                dict(row),
            )

    print("SQLite -> PostgreSQL 遷移完成")


if __name__ == "__main__":
    main()
