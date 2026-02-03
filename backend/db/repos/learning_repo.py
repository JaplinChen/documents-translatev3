from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.models.learning import LearningCandidate, LearningEvent, LearningStat


def get_candidate_by_key(
    session: Session,
    source_text: str,
    target_text: str,
    source_lang: str,
    target_lang: str,
    scope_type: str,
    scope_id: Optional[str],
) -> Optional[LearningCandidate]:
    stmt = (
        select(LearningCandidate)
        .where(LearningCandidate.source_text == source_text)
        .where(LearningCandidate.target_text == target_text)
        .where(LearningCandidate.source_lang == source_lang)
        .where(LearningCandidate.target_lang == target_lang)
        .where(LearningCandidate.scope_type == scope_type)
        .where(LearningCandidate.scope_id == scope_id)
    )
    return session.execute(stmt).scalars().first()


def upsert_candidate(
    session: Session,
    source_text: str,
    target_text: str,
    source_lang: str,
    target_lang: str,
    scope_type: str,
    scope_id: Optional[str],
    **fields,
) -> LearningCandidate:
    candidate = get_candidate_by_key(
        session, source_text, target_text, source_lang, target_lang, scope_type, scope_id
    )
    if candidate is None:
        candidate = LearningCandidate(
            source_text=source_text,
            target_text=target_text,
            source_lang=source_lang,
            target_lang=target_lang,
            scope_type=scope_type,
            scope_id=scope_id,
        )
        session.add(candidate)
    for key, value in fields.items():
        if hasattr(candidate, key):
            setattr(candidate, key, value)
    return candidate


def record_event(session: Session, **fields) -> LearningEvent:
    event = LearningEvent(**fields)
    session.add(event)
    return event


def record_stat(
    session: Session,
    stat_date: date,
    scope_type: str,
    scope_id: Optional[str],
    tm_hit_rate: Optional[float],
    glossary_hit_rate: Optional[float],
    overwrite_rate: Optional[float],
    auto_promotion_error_rate: Optional[float],
    wrong_suggestion_rate: Optional[float],
) -> LearningStat:
    stat = LearningStat(
        stat_date=stat_date,
        scope_type=scope_type,
        scope_id=scope_id,
        tm_hit_rate=tm_hit_rate,
        glossary_hit_rate=glossary_hit_rate,
        overwrite_rate=overwrite_rate,
        auto_promotion_error_rate=auto_promotion_error_rate,
        wrong_suggestion_rate=wrong_suggestion_rate,
    )
    session.add(stat)
    return stat
