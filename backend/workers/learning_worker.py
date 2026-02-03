from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.db.engine import get_session
from backend.db.models.learning import LearningEvent
from backend.db.repos.learning_repo import record_stat


def _rate(numerator: int, denominator: int) -> Optional[float]:
    if denominator <= 0:
        return None
    return round((numerator / denominator) * 100, 2)


def compute_daily_stats(session: Session, stat_date: date, scope_type: str, scope_id: Optional[str]):
    base_filters = [
        func.date(LearningEvent.created_at) == stat_date,
        LearningEvent.scope_type == scope_type,
        LearningEvent.scope_id == scope_id,
    ]

    total_lookups = session.execute(
        select(func.count()).select_from(LearningEvent).where(
            *base_filters, LearningEvent.event_type.in_(["lookup_hit_tm", "lookup_miss"])
        )
    ).scalar_one()

    tm_hits = session.execute(
        select(func.count()).select_from(LearningEvent).where(
            *base_filters, LearningEvent.event_type == "lookup_hit_tm"
        )
    ).scalar_one()

    glossary_hits = session.execute(
        select(func.count()).select_from(LearningEvent).where(
            *base_filters, LearningEvent.event_type == "lookup_hit_glossary"
        )
    ).scalar_one()

    overwrite_count = session.execute(
        select(func.count()).select_from(LearningEvent).where(
            *base_filters, LearningEvent.event_type == "overwrite"
        )
    ).scalar_one()

    promotions = session.execute(
        select(func.count()).select_from(LearningEvent).where(
            *base_filters, LearningEvent.event_type == "promote"
        )
    ).scalar_one()

    auto_promo_errors = session.execute(
        select(func.count()).select_from(LearningEvent).where(
            *base_filters, LearningEvent.event_type == "auto_promotion_error"
        )
    ).scalar_one()

    wrong_suggestions = session.execute(
        select(func.count()).select_from(LearningEvent).where(
            *base_filters, LearningEvent.event_type == "wrong_suggestion"
        )
    ).scalar_one()

    tm_hit_rate = _rate(tm_hits, total_lookups)
    glossary_hit_rate = _rate(glossary_hits, total_lookups)
    overwrite_rate = _rate(overwrite_count, max(tm_hits, 1))
    auto_promotion_error_rate = _rate(auto_promo_errors, max(promotions, 1))
    wrong_suggestion_rate = _rate(wrong_suggestions, max(total_lookups, 1))

    record_stat(
        session=session,
        stat_date=stat_date,
        scope_type=scope_type,
        scope_id=scope_id,
        tm_hit_rate=tm_hit_rate,
        glossary_hit_rate=glossary_hit_rate,
        overwrite_rate=overwrite_rate,
        auto_promotion_error_rate=auto_promotion_error_rate,
        wrong_suggestion_rate=wrong_suggestion_rate,
    )


def run_daily_stats(scope_type: str, scope_id: Optional[str], days_back: int = 1):
    target_date = date.today() - timedelta(days=days_back)
    session = get_session()
    try:
        compute_daily_stats(session, target_date, scope_type, scope_id)
        session.commit()
    finally:
        session.close()
