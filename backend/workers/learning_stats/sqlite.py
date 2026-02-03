from __future__ import annotations

from datetime import date
import sqlite3
from typing import Any

from backend.services import translation_memory as sqlite_tm

from .metrics import (
    EVENT_AUTO_PROMO_ERROR,
    EVENT_LOOKUP_HIT_GLOSSARY,
    EVENT_LOOKUP_HIT_TM,
    EVENT_LOOKUP_MISS,
    EVENT_OVERWRITE,
    EVENT_PROMOTE,
    EVENT_WRONG_SUGGESTION,
    rate,
)


def compute_daily_stats_sqlite(
    stat_date: date, scope_type: str = "project", scope_id: str | None = "default"
) -> dict[str, Any]:
    sqlite_tm._ensure_db()
    with sqlite3.connect(sqlite_tm.DB_PATH) as conn:
        base_params = [stat_date.strftime("%Y-%m-%d"), scope_type, scope_id]

        total_lookups = conn.execute(
            (
                "SELECT COUNT(1) FROM learning_events "
                "WHERE date(created_at) = ? AND scope_type = ? AND scope_id IS ? "
                "AND event_type IN (?, ?)"
            ),
            base_params + [EVENT_LOOKUP_HIT_TM, EVENT_LOOKUP_MISS],
        ).fetchone()[0]

        tm_hits = conn.execute(
            (
                "SELECT COUNT(1) FROM learning_events "
                "WHERE date(created_at) = ? AND scope_type = ? AND scope_id IS ? "
                "AND event_type = ?"
            ),
            base_params + [EVENT_LOOKUP_HIT_TM],
        ).fetchone()[0]

        glossary_hits = conn.execute(
            (
                "SELECT COUNT(1) FROM learning_events "
                "WHERE date(created_at) = ? AND scope_type = ? AND scope_id IS ? "
                "AND event_type = ?"
            ),
            base_params + [EVENT_LOOKUP_HIT_GLOSSARY],
        ).fetchone()[0]

        overwrite_count = conn.execute(
            (
                "SELECT COUNT(1) FROM learning_events "
                "WHERE date(created_at) = ? AND scope_type = ? AND scope_id IS ? "
                "AND event_type = ?"
            ),
            base_params + [EVENT_OVERWRITE],
        ).fetchone()[0]

        promotions = conn.execute(
            (
                "SELECT COUNT(1) FROM learning_events "
                "WHERE date(created_at) = ? AND scope_type = ? AND scope_id IS ? "
                "AND event_type = ?"
            ),
            base_params + [EVENT_PROMOTE],
        ).fetchone()[0]

        auto_promo_errors = conn.execute(
            (
                "SELECT COUNT(1) FROM learning_events "
                "WHERE date(created_at) = ? AND scope_type = ? AND scope_id IS ? "
                "AND event_type = ?"
            ),
            base_params + [EVENT_AUTO_PROMO_ERROR],
        ).fetchone()[0]

        wrong_suggestions = conn.execute(
            (
                "SELECT COUNT(1) FROM learning_events "
                "WHERE date(created_at) = ? AND scope_type = ? AND scope_id IS ? "
                "AND event_type = ?"
            ),
            base_params + [EVENT_WRONG_SUGGESTION],
        ).fetchone()[0]

        tm_hit_rate = rate(tm_hits, total_lookups)
        glossary_hit_rate = rate(glossary_hits, total_lookups)
        overwrite_rate = rate(overwrite_count, max(tm_hits, 1))
        auto_promotion_error_rate = rate(auto_promo_errors, max(promotions, 1))
        wrong_suggestion_rate = rate(wrong_suggestions, max(total_lookups, 1))

        conn.execute(
            (
                "INSERT INTO learning_stats "
                "(stat_date, scope_type, scope_id, tm_hit_rate, glossary_hit_rate, "
                "overwrite_rate, auto_promotion_error_rate, wrong_suggestion_rate) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            ),
            (
                stat_date.strftime("%Y-%m-%d"),
                scope_type,
                scope_id,
                tm_hit_rate,
                glossary_hit_rate,
                overwrite_rate,
                auto_promotion_error_rate,
                wrong_suggestion_rate,
            ),
        )
        conn.commit()

    return {
        "tm_hit_rate": tm_hit_rate,
        "glossary_hit_rate": glossary_hit_rate,
        "overwrite_rate": overwrite_rate,
        "auto_promotion_error_rate": auto_promotion_error_rate,
        "wrong_suggestion_rate": wrong_suggestion_rate,
    }
