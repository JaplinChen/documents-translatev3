from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import text

from backend.db.engine import get_engine

from .db import _ensure_db
from .learning import _record_learning_event
from .preserve_terms import _get_preserve_terms, _is_preserve_term
from .utils import _hash_text, _is_low_quality_tm, _normalize_glossary_text, _resolve_context_scope


def save_tm(
    source_lang: str,
    target_lang: str,
    text_value: str,
    translated: str,
    context: dict | None = None,
) -> None:
    if not text_value or not translated:
        return
    if _is_low_quality_tm(text_value, translated):
        return
    _ensure_db()
    source_text = text_value.strip()
    target_text = translated.strip()
    if not source_text or not target_text:
        return
    preserve_terms = _get_preserve_terms()
    if _is_preserve_term(source_text, preserve_terms):
        return
    key = _hash_text(source_lang, target_lang, text_value, context=context)
    scope_type, scope_id, domain, category = _resolve_context_scope(context)
    engine = get_engine()
    with engine.begin() as conn:
        existing = conn.execute(
            text("SELECT id, target_text FROM tm WHERE hash = :hash"),
            {"hash": key},
        ).fetchone()
        if existing and existing[1] != target_text:
            conn.execute(
                text("UPDATE tm SET overwrite_count = overwrite_count + 1 WHERE id = :id"),
                {"id": existing[0]},
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
            text(
                "SELECT 1 FROM glossary "
                "WHERE source_lang = :source_lang AND target_lang = :target_lang "
                "AND source_text = :source_text LIMIT 1"
            ),
            {
                "source_lang": source_lang,
                "target_lang": target_lang,
                "source_text": normalized_source,
            },
        )
        if cur.fetchone():
            return
        cur = conn.execute(
            text("SELECT 1 FROM tm WHERE source_text = :source_text AND target_text = :target_text LIMIT 1"),
            {"source_text": source_text, "target_text": target_text},
        )
        if cur.fetchone():
            return
        conn.execute(
            text(
                "INSERT INTO tm "
                "(source_lang, target_lang, source_text, target_text, "
                "domain, category, scope_type, scope_id, hash, created_at) "
                "VALUES (:source_lang, :target_lang, :source_text, :target_text, "
                ":domain, :category, :scope_type, :scope_id, :hash, now()) "
                "ON CONFLICT (hash) DO UPDATE SET "
                "target_text = EXCLUDED.target_text, "
                "domain = EXCLUDED.domain, "
                "category = EXCLUDED.category, "
                "scope_type = EXCLUDED.scope_type, "
                "scope_id = EXCLUDED.scope_id"
            ),
            {
                "source_lang": source_lang,
                "target_lang": target_lang,
                "source_text": source_text,
                "target_text": target_text,
                "domain": domain,
                "category": category,
                "scope_type": scope_type,
                "scope_id": scope_id,
                "hash": key,
            },
        )
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
    engine = get_engine()
    with engine.begin() as conn:
        for source_lang, target_lang, source_text, target_text in entries:
            key = _hash_text(source_lang, target_lang, source_text)
            conn.execute(
                text(
                    "INSERT INTO tm "
                    "(source_lang, target_lang, source_text, target_text, hash, created_at) "
                    "VALUES (:source_lang, :target_lang, :source_text, :target_text, :hash, now()) "
                    "ON CONFLICT (hash) DO UPDATE SET target_text = EXCLUDED.target_text"
                ),
                {
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "source_text": source_text,
                    "target_text": target_text,
                    "hash": key,
                },
            )
