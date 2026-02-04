from __future__ import annotations

import sqlite3

from backend.services.language_detect import detect_language

from .db import DB_PATH, _ensure_db
from .preserve_terms import _get_preserve_terms, _is_preserve_term


def get_glossary_terms(
    source_lang: str,
    target_lang: str,
) -> list[tuple[str, str]]:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "SELECT source_text, target_text FROM glossary "
            "WHERE source_lang = ? AND target_lang = ? "
            "ORDER BY priority DESC, id ASC",
            (source_lang, target_lang),
        )
        rows = cur.fetchall()
    return [(row[0], row[1]) for row in rows]


def get_glossary_terms_any(target_lang: str) -> list[tuple[str, str]]:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "SELECT source_text, target_text FROM glossary "
            "WHERE target_lang = ? "
            "ORDER BY priority DESC, id ASC",
            (target_lang,),
        )
        rows = cur.fetchall()
    return [(row[0], row[1]) for row in rows]


def get_glossary(limit: int = 200, offset: int = 0) -> list[dict]:
    _ensure_db()
    preserve_terms = _get_preserve_terms()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            (
                "SELECT g.id, g.source_lang, g.target_lang, g.source_text, "
                "g.target_text, g.priority, g.category_id, c.name as category_name, "
                "g.domain, g.category, g.scope_type, g.scope_id, g.status, "
                "g.hit_count, g.overwrite_count, g.last_hit_at, g.created_at "
                "FROM glossary g LEFT JOIN tm_categories c ON g.category_id = c.id "
                "ORDER BY g.priority DESC, g.id ASC LIMIT ? OFFSET ?"
            ),
            (limit, offset),
        )
        rows = cur.fetchall()
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
            conn.executemany(
                "DELETE FROM glossary WHERE id = ?",
                [(entry_id,) for entry_id in delete_ids],
            )
        update_map = {}
        update_target_map = {}
        if source_updates:
            for lang, entry_id in source_updates:
                row = conn.execute(
                    "SELECT source_text, target_lang FROM glossary WHERE id = ?",
                    (entry_id,),
                ).fetchone()
                if not row:
                    continue
                source_text, target_lang = row
                duplicate = conn.execute(
                    (
                        "SELECT id FROM glossary "
                        "WHERE source_lang = ? AND target_lang = ? AND source_text = ? "
                        "AND id != ? LIMIT 1"
                    ),
                    (lang, target_lang, source_text, entry_id),
                ).fetchone()
                if duplicate:
                    conn.execute("DELETE FROM glossary WHERE id = ?", (entry_id,))
                    delete_ids.append(entry_id)
                    continue
                conn.execute(
                    "UPDATE glossary SET source_lang = ? WHERE id = ?",
                    (lang, entry_id),
                )
                update_map[entry_id] = lang
        if target_updates:
            for lang, entry_id in target_updates:
                conn.execute(
                    "UPDATE glossary SET target_lang = ? WHERE id = ?",
                    (lang, entry_id),
                )
                update_target_map[entry_id] = lang
        if source_updates or target_updates:
            conn.commit()
        if delete_ids and not (source_updates or target_updates):
            conn.commit()
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
    preserve_terms = _get_preserve_terms()
    with sqlite3.connect(DB_PATH) as conn:
        if not preserve_terms:
            cur = conn.execute("SELECT COUNT(1) FROM glossary")
        else:
            cur = conn.execute(
                (
                    "SELECT COUNT(1) FROM glossary g "
                    "WHERE NOT EXISTS ("
                    "  SELECT 1 FROM preserve_terms p "
                    "  WHERE (p.case_sensitive = 1 AND p.term = g.source_text) "
                    "     OR (p.case_sensitive = 0 AND lower(p.term) = lower(g.source_text))"
                    ")"
                )
            )
        row = cur.fetchone()
    return int(row[0] or 0)
