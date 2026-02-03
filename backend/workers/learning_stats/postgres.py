from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import text

from backend.db.engine import get_engine

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


def compute_daily_stats_pg(
    stat_date: date, scope_type: str = "project", scope_id: str | None = "default"
) -> dict[str, Any]:
    engine = get_engine()
    base_params = {
        "stat_date": stat_date.strftime("%Y-%m-%d"),
        "scope_type": scope_type,
        "scope_id": scope_id,
    }
    with engine.begin() as conn:
        total_lookups = conn.execute(
            text(
                "SELECT COUNT(1) FROM learning_events "
                "WHERE DATE(created_at) = :stat_date AND scope_type = :scope_type "
                "AND scope_id IS NOT DISTINCT FROM :scope_id "
                "AND event_type IN (:hit_tm, :miss)"
            ),
            {**base_params, "hit_tm": EVENT_LOOKUP_HIT_TM, "miss": EVENT_LOOKUP_MISS},
        ).fetchone()[0]

        tm_hits = conn.execute(
            text(
                "SELECT COUNT(1) FROM learning_events "
                "WHERE DATE(created_at) = :stat_date AND scope_type = :scope_type "
                "AND scope_id IS NOT DISTINCT FROM :scope_id "
                "AND event_type = :event_type"
            ),
            {**base_params, "event_type": EVENT_LOOKUP_HIT_TM},
        ).fetchone()[0]

        glossary_hits = conn.execute(
            text(
                "SELECT COUNT(1) FROM learning_events "
                "WHERE DATE(created_at) = :stat_date AND scope_type = :scope_type "
                "AND scope_id IS NOT DISTINCT FROM :scope_id "
                "AND event_type = :event_type"
            ),
            {**base_params, "event_type": EVENT_LOOKUP_HIT_GLOSSARY},
        ).fetchone()[0]

        overwrite_count = conn.execute(
            text(
                "SELECT COUNT(1) FROM learning_events "
                "WHERE DATE(created_at) = :stat_date AND scope_type = :scope_type "
                "AND scope_id IS NOT DISTINCT FROM :scope_id "
                "AND event_type = :event_type"
            ),
            {**base_params, "event_type": EVENT_OVERWRITE},
        ).fetchone()[0]

        promotions = conn.execute(
            text(
                "SELECT COUNT(1) FROM learning_events "
                "WHERE DATE(created_at) = :stat_date AND scope_type = :scope_type "
                "AND scope_id IS NOT DISTINCT FROM :scope_id "
                "AND event_type = :event_type"
            ),
            {**base_params, "event_type": EVENT_PROMOTE},
        ).fetchone()[0]

        auto_promo_errors = conn.execute(
            text(
                "SELECT COUNT(1) FROM learning_events "
                "WHERE DATE(created_at) = :stat_date AND scope_type = :scope_type "
                "AND scope_id IS NOT DISTINCT FROM :scope_id "
                "AND event_type = :event_type"
            ),
            {**base_params, "event_type": EVENT_AUTO_PROMO_ERROR},
        ).fetchone()[0]

        wrong_suggestions = conn.execute(
            text(
                "SELECT COUNT(1) FROM learning_events "
                "WHERE DATE(created_at) = :stat_date AND scope_type = :scope_type "
                "AND scope_id IS NOT DISTINCT FROM :scope_id "
                "AND event_type = :event_type"
            ),
            {**base_params, "event_type": EVENT_WRONG_SUGGESTION},
        ).fetchone()[0]

        tm_hit_rate = rate(tm_hits, total_lookups)
        glossary_hit_rate = rate(glossary_hits, total_lookups)
        overwrite_rate = rate(overwrite_count, max(tm_hits, 1))
        auto_promotion_error_rate = rate(auto_promo_errors, max(promotions, 1))
        wrong_suggestion_rate = rate(wrong_suggestions, max(total_lookups, 1))

        conn.execute(
            text(
                "INSERT INTO learning_stats "
                "(stat_date, scope_type, scope_id, tm_hit_rate, glossary_hit_rate, "
                "overwrite_rate, auto_promotion_error_rate, wrong_suggestion_rate, created_at) "
                "VALUES (:stat_date, :scope_type, :scope_id, :tm_hit_rate, :glossary_hit_rate, "
                ":overwrite_rate, :auto_promotion_error_rate, :wrong_suggestion_rate, now())"
            ),
            {
                **base_params,
                "tm_hit_rate": tm_hit_rate,
                "glossary_hit_rate": glossary_hit_rate,
                "overwrite_rate": overwrite_rate,
                "auto_promotion_error_rate": auto_promotion_error_rate,
                "wrong_suggestion_rate": wrong_suggestion_rate,
            },
        )

    return {
        "tm_hit_rate": tm_hit_rate,
        "glossary_hit_rate": glossary_hit_rate,
        "overwrite_rate": overwrite_rate,
        "auto_promotion_error_rate": auto_promotion_error_rate,
        "wrong_suggestion_rate": wrong_suggestion_rate,
    }
