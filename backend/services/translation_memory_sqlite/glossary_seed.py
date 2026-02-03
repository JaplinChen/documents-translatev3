from __future__ import annotations

import sqlite3
from collections.abc import Iterable

from .db import DB_PATH, _ensure_db
from .preserve_terms import _get_preserve_terms, _is_preserve_term
from .utils import _normalize_glossary_text


def seed_glossary(
    entries: Iterable[tuple[str, str, str, str, int | None]],
) -> None:
    _ensure_db()
    preserve_terms = _get_preserve_terms()
    with sqlite3.connect(DB_PATH) as conn:
        for (
            source_lang,
            target_lang,
            source_text,
            target_text,
            priority,
        ) in entries:
            source_text = _normalize_glossary_text(source_text)
            if _is_preserve_term(source_text, preserve_terms):
                continue
            conn.execute(
                (
                    "DELETE FROM glossary "
                    "WHERE source_lang = ? AND target_lang = ? "
                    "AND source_text = ?"
                ),
                (source_lang, target_lang, source_text),
            )
            conn.execute(
                (
                    "INSERT INTO glossary "
                    "(source_lang, target_lang, source_text, "
                    "target_text, priority) "
                    "VALUES (?, ?, ?, ?, COALESCE(?, 0))"
                ),
                (
                    source_lang,
                    target_lang,
                    source_text,
                    _normalize_glossary_text(target_text),
                    priority,
                ),
            )
        conn.commit()
