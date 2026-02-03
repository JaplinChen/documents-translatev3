from __future__ import annotations

from sqlalchemy import text

from backend.db.engine import get_engine
from backend.services.tm_matcher import fuzzy_match, normalize_text

from .db import _ensure_db
from .learning import _record_learning_event
from .utils import _hash_text, _resolve_context_scope


def _record_tm_hit(entry_id: int) -> None:
    try:
        _ensure_db()
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE tm SET hit_count = hit_count + 1, last_hit_at = now() "
                    "WHERE id = :id"
                ),
                {"id": entry_id},
            )
    except Exception:
        return


def lookup_tm(
    source_lang: str,
    target_lang: str,
    text_value: str,
    context: dict | None = None,
    use_fuzzy: bool = False,
) -> str | None:
    _ensure_db()
    scope_type, scope_id, domain, category = _resolve_context_scope(context)
    key = _hash_text(source_lang, target_lang, text_value, context=context)
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                "SELECT id, target_text FROM tm "
                "WHERE hash = :hash AND status = 'active' "
                "AND (scope_type = :scope_type OR scope_type IS NULL) "
                "AND (scope_id = :scope_id OR scope_id IS NULL)"
            ),
            {"hash": key, "scope_type": scope_type, "scope_id": scope_id},
        ).fetchone()
    if row:
        _record_tm_hit(row[0])
        _record_learning_event(
            "lookup_hit_tm",
            source_text=text_value,
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
            source_text=text_value,
            source_lang=source_lang,
            target_lang=target_lang,
            entity_type="tm",
            scope_type=scope_type,
            scope_id=scope_id,
        )
        return None
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT id, source_text, target_text, domain, category, scope_type, scope_id "
                "FROM tm "
                "WHERE source_lang = :source_lang AND target_lang = :target_lang "
                "AND status = 'active' "
                "AND (scope_type = :scope_type OR scope_type IS NULL) "
                "AND (scope_id = :scope_id OR scope_id IS NULL) "
                "ORDER BY id DESC LIMIT 500"
            ),
            {
                "source_lang": source_lang,
                "target_lang": target_lang,
                "scope_type": scope_type,
                "scope_id": scope_id,
            },
        ).fetchall()
    if not rows:
        _record_learning_event(
            "lookup_miss",
            source_text=text_value,
            source_lang=source_lang,
            target_lang=target_lang,
            entity_type="tm",
            scope_type=scope_type,
            scope_id=scope_id,
        )
        return None
    normalized_query = normalize_text(text_value)
    for entry_id, source_text, target_text, _, _, _, _ in rows:
        if normalize_text(source_text) == normalized_query:
            _record_tm_hit(entry_id)
            _record_learning_event(
                "lookup_hit_tm",
                source_text=text_value,
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
        query=text_value,
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
            source_text=text_value,
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
        source_text=text_value,
        source_lang=source_lang,
        target_lang=target_lang,
        entity_type="tm",
        scope_type=scope_type,
        scope_id=scope_id,
    )
    return None
