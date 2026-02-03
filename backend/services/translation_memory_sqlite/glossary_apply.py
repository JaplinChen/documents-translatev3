from __future__ import annotations

import sqlite3

from .db import DB_PATH, _ensure_db
from .learning import _record_learning_event


def apply_glossary(source_lang: str, target_lang: str, text: str) -> str:
    if not text:
        return text
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "SELECT source_text, target_text FROM glossary "
            "WHERE source_lang = ? AND target_lang = ? "
            "ORDER BY priority DESC, id ASC",
            (source_lang, target_lang),
        )
        rows = cur.fetchall()
    updated = text
    for source_text, target_text in rows:
        updated = updated.replace(source_text, target_text)
    if updated != text:
        _record_learning_event(
            "lookup_hit_glossary",
            source_text=text,
            target_text=updated,
            source_lang=source_lang,
            target_lang=target_lang,
            entity_type="glossary",
        )
    return updated
