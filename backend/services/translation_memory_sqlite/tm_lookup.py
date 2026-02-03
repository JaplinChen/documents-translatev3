from __future__ import annotations

import sqlite3

from backend.services.tm_matcher import fuzzy_match, normalize_text

from .db import DB_PATH, _ensure_db
from .learning import _record_learning_event
from .utils import _hash_text, _resolve_context_scope


def _record_tm_hit(entry_id: int) -> None:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "UPDATE tm SET hit_count = hit_count + 1, last_hit_at = CURRENT_TIMESTAMP WHERE id = ?",
                (entry_id,),
            )
            conn.commit()
    except Exception:
        return


def lookup_tm(
    source_lang: str,
    target_lang: str,
    text: str,
    context: dict | None = None,
    use_fuzzy: bool = False,
) -> str | None:
    _ensure_db()
    scope_type, scope_id, domain, category = _resolve_context_scope(context)
    key = _hash_text(source_lang, target_lang, text, context=context)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            (
                "SELECT id, target_text FROM tm "
                "WHERE hash = ? AND status = 'active' "
                "AND (scope_type = ? OR scope_type IS NULL) "
                "AND (scope_id = ? OR scope_id IS NULL)"
            ),
            (key, scope_type, scope_id),
        )
        row = cur.fetchone()
        if row:
            _record_tm_hit(row[0])
            _record_learning_event(
                "lookup_hit_tm",
                source_text=text,
                target_text=row[1],
                source_lang=source_lang,
                target_lang=target_lang,
                entity_type="tm",
                entity_id=row[0],
                scope_type=scope_type,
                scope_id=scope_id,
            )
            return row[1]
        if not use_fuzzy:
            _record_learning_event(
                "lookup_miss",
                source_text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                entity_type="tm",
                scope_type=scope_type,
                scope_id=scope_id,
            )
            return None
        cur = conn.execute(
            "SELECT id, source_text, target_text, domain, category, scope_type, scope_id FROM tm "
            "WHERE source_lang = ? AND target_lang = ? AND status = 'active' "
            "AND (scope_type = ? OR scope_type IS NULL) "
            "AND (scope_id = ? OR scope_id IS NULL) "
            "ORDER BY id DESC LIMIT 500",
            (source_lang, target_lang, scope_type, scope_id),
        )
        rows = cur.fetchall()
    if not rows:
        _record_learning_event(
            "lookup_miss",
            source_text=text,
            source_lang=source_lang,
            target_lang=target_lang,
            entity_type="tm",
            scope_type=scope_type,
            scope_id=scope_id,
        )
        return None
    normalized_query = normalize_text(text)
    for entry_id, source_text, target_text, _, _, _, _ in rows:
        if normalize_text(source_text) == normalized_query:
            _record_tm_hit(entry_id)
            _record_learning_event(
                "lookup_hit_tm",
                source_text=text,
                target_text=target_text,
                source_lang=source_lang,
                target_lang=target_lang,
                entity_type="tm",
                entity_id=entry_id,
                scope_type=scope_type,
                scope_id=scope_id,
            )
            return target_text
    candidates = [
        {
            "id": entry_id,
            "source_text": source_text,
            "target_text": target_text,
            "domain": row_domain,
            "category": row_category,
            "scope_type": row_scope_type,
            "scope_id": row_scope_id,
        }
        for (
            entry_id,
            source_text,
            target_text,
            row_domain,
            row_category,
            row_scope_type,
            row_scope_id,
        ) in rows
    ]
    results = fuzzy_match(
        query=text,
        candidates=candidates,
        scope={"domain": domain, "category": category, "scope_type": scope_type, "scope_id": scope_id},
        min_score=0.78,
        limit=1,
    )
    if results:
        best = results[0][1]
        entry_id = best.get("id")
        if entry_id:
            _record_tm_hit(entry_id)
        _record_learning_event(
            "lookup_hit_tm",
            source_text=text,
            target_text=best.get("target_text"),
            source_lang=source_lang,
            target_lang=target_lang,
            entity_type="tm",
            entity_id=entry_id,
            scope_type=scope_type,
            scope_id=scope_id,
        )
        return best.get("target_text")
    _record_learning_event(
        "lookup_miss",
        source_text=text,
        source_lang=source_lang,
        target_lang=target_lang,
        entity_type="tm",
        scope_type=scope_type,
        scope_id=scope_id,
    )
    return None
