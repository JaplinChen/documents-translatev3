from __future__ import annotations

import sqlite3
from collections.abc import Iterable

from .db import DB_PATH, _ensure_db
from .learning import _record_learning_event
from .preserve_terms import _get_preserve_terms, _is_preserve_term
from .utils import _hash_text, _is_low_quality_tm, _normalize_glossary_text, _resolve_context_scope


def save_tm(
    source_lang: str,
    target_lang: str,
    text: str,
    translated: str,
    context: dict | None = None,
) -> None:
    if not text or not translated:
        return
    if _is_low_quality_tm(text, translated):
        print(f"攔截低質量 TM 寫入: {text} -> {translated}")
        return
    _ensure_db()
    source_text = text.strip()
    target_text = translated.strip()
    if not source_text or not target_text:
        return
    preserve_terms = _get_preserve_terms()
    if _is_preserve_term(source_text, preserve_terms):
        return
    key = _hash_text(source_lang, target_lang, text, context=context)
    scope_type, scope_id, domain, category = _resolve_context_scope(context)
    with sqlite3.connect(DB_PATH) as conn:
        existing = conn.execute(
            "SELECT id, target_text FROM tm WHERE hash = ?",
            (key,),
        ).fetchone()
        if existing and existing[1] != target_text:
            conn.execute(
                "UPDATE tm SET overwrite_count = overwrite_count + 1 WHERE id = ?",
                (existing[0],),
            )
            _record_learning_event(
                "overwrite",
                source_text=source_text,
                target_text=target_text,
                source_lang=source_lang,
                target_lang=target_lang,
                entity_type="tm",
                entity_id=existing[0],
                scope_type=scope_type,
                scope_id=scope_id,
            )
        normalized_source = _normalize_glossary_text(source_text)
        cur = conn.execute(
            (
                "SELECT 1 FROM glossary "
                "WHERE source_lang = ? AND target_lang = ? AND source_text = ? "
                "LIMIT 1"
            ),
            (source_lang, target_lang, normalized_source),
        )
        if cur.fetchone():
            return
        cur = conn.execute(
            "SELECT 1 FROM tm WHERE source_text = ? AND target_text = ? LIMIT 1",
            (source_text, target_text),
        )
        if cur.fetchone():
            return
        conn.execute(
            (
                "INSERT OR REPLACE INTO tm "
                "(source_lang, target_lang, source_text, target_text, "
                "domain, category, scope_type, scope_id, hash) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
            ),
            (
                source_lang,
                target_lang,
                text,
                translated,
                domain,
                category,
                scope_type,
                scope_id,
                key,
            ),
        )
        conn.commit()
    _record_learning_event(
        "ingest",
        source_text=source_text,
        target_text=target_text,
        source_lang=source_lang,
        target_lang=target_lang,
        entity_type="tm",
        scope_type=scope_type,
        scope_id=scope_id,
    )


def seed_tm(entries: Iterable[tuple[str, str, str, str]]) -> None:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        for source_lang, target_lang, source_text, target_text in entries:
            key = _hash_text(source_lang, target_lang, source_text)
            conn.execute(
                (
                    "INSERT OR REPLACE INTO tm "
                    "(source_lang, target_lang, source_text, "
                    "target_text, hash) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                (source_lang, target_lang, source_text, target_text, key),
            )
        conn.commit()
