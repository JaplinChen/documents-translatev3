from __future__ import annotations

from sqlalchemy import text

from backend.db.engine import get_engine
from backend.services.language_detect import detect_language

from .db import _ensure_db
from .preserve_terms import _get_preserve_terms, _is_preserve_term


def get_glossary(limit: int = 200, offset: int = 0) -> list[dict]:
    _ensure_db()
    preserve_terms = _get_preserve_terms()
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT g.id, g.source_lang, g.target_lang, g.source_text, "
                "g.target_text, g.priority, g.category_id, c.name as category_name, "
                "g.domain, g.category, g.scope_type, g.scope_id, g.status, "
                "g.hit_count, g.overwrite_count, g.last_hit_at, g.created_at "
                "FROM glossary g LEFT JOIN tm_categories c ON g.category_id = c.id "
                "ORDER BY g.priority DESC, g.id ASC LIMIT :limit OFFSET :offset"
            ),
            {"limit": limit, "offset": offset},
        ).fetchall()
        delete_ids: list[int] = []
        source_updates: list[tuple[str, int]] = []
        target_updates: list[tuple[str, int]] = []
        for row in rows:
            entry_id = row[0]
            source_lang = row[1]
            target_lang = row[2]
            source_text = row[3]
            target_text = row[4]
            if _is_preserve_term(source_text, preserve_terms):
                delete_ids.append(entry_id)
                continue
            if not source_lang or source_lang in {"auto", "unknown"}:
                detected = detect_language(source_text or "")
                if detected and detected != source_lang:
                    source_updates.append((detected, entry_id))
            if not target_lang or target_lang in {"auto", "unknown"}:
                detected_target = detect_language(target_text or "")
                if detected_target and detected_target != target_lang:
                    target_updates.append((detected_target, entry_id))
        if delete_ids:
            conn.execute(
                text("DELETE FROM glossary WHERE id = ANY(:ids)"),
                {"ids": delete_ids},
            )
        update_map: dict[int, str] = {}
        update_target_map: dict[int, str] = {}
        if source_updates:
            for lang, entry_id in source_updates:
                row = conn.execute(
                    text("SELECT source_text, target_lang FROM glossary WHERE id = :id"),
                    {"id": entry_id},
                ).fetchone()
                if not row:
                    continue
                source_text, target_lang = row
                duplicate = conn.execute(
                    text(
                        "SELECT id FROM glossary "
                        "WHERE source_lang = :source_lang AND target_lang = :target_lang "
                        "AND source_text = :source_text AND id != :id LIMIT 1"
                    ),
                    {
                        "source_lang": lang,
                        "target_lang": target_lang,
                        "source_text": source_text,
                        "id": entry_id,
                    },
                ).fetchone()
                if duplicate:
                    conn.execute(text("DELETE FROM glossary WHERE id = :id"), {"id": entry_id})
                    delete_ids.append(entry_id)
                    continue
                conn.execute(
                    text("UPDATE glossary SET source_lang = :source_lang WHERE id = :id"),
                    {"source_lang": lang, "id": entry_id},
                )
                update_map[entry_id] = lang
        if target_updates:
            for lang, entry_id in target_updates:
                conn.execute(
                    text("UPDATE glossary SET target_lang = :target_lang WHERE id = :id"),
                    {"target_lang": lang, "id": entry_id},
                )
                update_target_map[entry_id] = lang
    return [
        {
            "id": row[0],
            "source_lang": update_map.get(row[0], row[1]) or "auto",
            "target_lang": update_target_map.get(row[0], row[2]) or "unknown",
            "source_text": row[3],
            "target_text": row[4],
            "priority": row[5],
            "category_id": row[6],
            "category_name": row[7],
            "domain": row[8],
            "category": row[9],
            "scope_type": row[10],
            "scope_id": row[11],
            "status": row[12],
            "hit_count": row[13],
            "overwrite_count": row[14],
            "last_hit_at": row[15],
            "created_at": row[16],
        }
        for row in rows
        if row[0] not in delete_ids
    ]


def get_glossary_count() -> int:
    _ensure_db()
    engine = get_engine()
    preserve_terms = _get_preserve_terms()
    with engine.begin() as conn:
        if not preserve_terms:
            row = conn.execute(text("SELECT COUNT(1) FROM glossary")).fetchone()
            return int(row[0] or 0)
        rows = conn.execute(text("SELECT source_text FROM glossary")).fetchall()
    count = 0
    for row in rows:
        if not _is_preserve_term(row[0], preserve_terms):
            count += 1
    return count


def get_glossary_terms(
    source_lang: str,
    target_lang: str,
) -> list[tuple[str, str]]:
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
    return [(row[0], row[1]) for row in rows]


def get_glossary_terms_any(target_lang: str) -> list[tuple[str, str]]:
    _ensure_db()
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT source_text, target_text FROM glossary "
                "WHERE target_lang = :target_lang "
                "ORDER BY priority DESC, id ASC"
            ),
            {"target_lang": target_lang},
        ).fetchall()
    return [(row[0], row[1]) for row in rows]
