from __future__ import annotations

from sqlalchemy import text

from backend.db.engine import get_engine

from .db import _ensure_db
from .glossary_admin import upsert_glossary
from .learning import _record_learning_event


def record_term_feedback(
    source_text: str,
    target_text: str,
    source_lang: str | None = None,
    target_lang: str | None = "zh-TW",
) -> None:
    _ensure_db()
    if not source_text or not target_text:
        return
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                "INSERT INTO term_feedback "
                "(source_text, target_text, source_lang, target_lang, correction_count, last_corrected_at) "
                "VALUES (:source_text, :target_text, :source_lang, :target_lang, 1, now()) "
                "ON CONFLICT (source_text, target_text, source_lang, target_lang) DO UPDATE SET "
                "correction_count = term_feedback.correction_count + 1, "
                "last_corrected_at = now() "
                "RETURNING correction_count"
            ),
            {
                "source_text": source_text.strip(),
                "target_text": target_text.strip(),
                "source_lang": source_lang,
                "target_lang": target_lang,
            },
        ).fetchone()
        count = row[0] if row else 1
    _record_learning_event(
        "feedback",
        source_text=source_text.strip(),
        target_text=target_text.strip(),
        source_lang=source_lang,
        target_lang=target_lang,
        entity_type="term_feedback",
        scope_type="project",
        scope_id="default",
    )
    if count >= 3:
        upsert_glossary(
            {
                "source_lang": source_lang or "auto",
                "target_lang": target_lang or "zh-TW",
                "source_text": source_text.strip(),
                "target_text": target_text.strip(),
                "priority": 10,
                "category_id": None,
            }
        )
        _record_learning_event(
            "promote",
            source_text=source_text.strip(),
            target_text=target_text.strip(),
            source_lang=source_lang,
            target_lang=target_lang,
            entity_type="glossary",
            scope_type="project",
            scope_id="default",
        )


def get_learned_terms(
    target_lang: str = "zh-TW", min_count: int = 1, limit: int = 50
) -> list[dict]:
    _ensure_db()
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT source_text, target_text, correction_count "
                "FROM term_feedback WHERE target_lang = :target_lang "
                "ORDER BY correction_count DESC, last_corrected_at DESC LIMIT :limit"
            ),
            {"target_lang": target_lang, "limit": limit},
        ).fetchall()
    return [
        {"source": r[0], "target": r[1], "count": r[2]}
        for r in rows
        if r[2] >= min_count
    ]
