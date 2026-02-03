from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import text

from backend.db.engine import get_engine

from .db import _ensure_db
from .preserve_terms import _get_preserve_terms, _is_preserve_term
from .utils import _normalize_glossary_text


def seed_glossary(entries: Iterable[tuple[str, str, str, str, int]]) -> None:
    _ensure_db()
    preserve_terms = _get_preserve_terms()
    engine = get_engine()
    with engine.begin() as conn:
        for source_lang, target_lang, source_text, target_text, priority in entries:
            source_text = _normalize_glossary_text(source_text)
            if _is_preserve_term(source_text, preserve_terms):
                continue
            conn.execute(
                text(
                    "INSERT INTO glossary "
                    "(source_lang, target_lang, source_text, target_text, priority, created_at) "
                    "VALUES (:source_lang, :target_lang, :source_text, :target_text, :priority, now()) "
                    "ON CONFLICT (source_lang, target_lang, source_text) DO UPDATE SET "
                    "target_text = EXCLUDED.target_text, priority = EXCLUDED.priority"
                ),
                {
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "source_text": source_text,
                    "target_text": _normalize_glossary_text(target_text),
                    "priority": priority or 0,
                },
            )
