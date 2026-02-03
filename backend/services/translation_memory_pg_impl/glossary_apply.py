from __future__ import annotations

from sqlalchemy import text

from backend.db.engine import get_engine

from .db import _ensure_db
from .learning import _record_learning_event


def apply_glossary(source_lang: str, target_lang: str, text_value: str) -> str:
    if not text_value:
        return text_value
    _ensure_db()
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT source_text, target_text FROM glossary "
                "WHERE source_lang = :source_lang AND target_lang = :target_lang "
                "ORDER BY priority DESC, id ASC"
            ),
            {"source_lang": source_lang, "target_lang": target_lang},
        ).fetchall()
    updated = text_value
    for source_text, target_text in rows:
        updated = updated.replace(source_text, target_text)
    if updated != text_value:
        _record_learning_event(
            "lookup_hit_glossary",
            source_text=text_value,
            target_text=updated,
            source_lang=source_lang,
            target_lang=target_lang,
            entity_type="glossary",
        )
    return updated
