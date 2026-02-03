from __future__ import annotations

import sqlite3

import backend.services.term_repository as term_repo

from .db import DB_PATH, _ensure_db
from .preserve_terms import _get_preserve_terms, _is_preserve_term
from .utils import _normalize_glossary_text


def upsert_glossary(entry: dict) -> None:
    _ensure_db()
    preserve_terms = _get_preserve_terms()
    entry_source = _normalize_glossary_text(entry.get("source_text", ""))
    entry_target = _normalize_glossary_text(entry.get("target_text", ""))
    if _is_preserve_term(entry_source, preserve_terms):
        return
    entry_id = entry.get("id")
    with sqlite3.connect(DB_PATH) as conn:
        if entry_id:
            # Explicit update by ID
            conn.execute(
                (
                    "UPDATE glossary SET "
                    "source_lang = ?, target_lang = ?, source_text = ?, "
                    "target_text = ?, priority = ?, category_id = ?, "
                    "domain = ?, category = ?, scope_type = ?, scope_id = ? "
                    "WHERE id = ?"
                ),
                (
                    entry.get("source_lang"),
                    entry.get("target_lang"),
                    entry_source,
                    entry_target,
                    entry.get("priority", 0),
                    entry.get("category_id"),
                    entry.get("domain"),
                    entry.get("category"),
                    entry.get("scope_type") or "project",
                    entry.get("scope_id") or "default",
                    entry_id,
                ),
            )
            print(f"Glossary updated by ID: {entry_id}")
        else:
            # Legacy INSERT OR REPLACE by source/target unique constraints
            conn.execute(
                (
                    "DELETE FROM glossary WHERE source_lang = ? AND target_lang = ? AND source_text = ?"
                ),
                (
                    entry.get("source_lang"),
                    entry.get("target_lang"),
                    entry_source,
                ),
            )
            conn.execute(
                (
                    "INSERT INTO glossary "
                    "(source_lang, target_lang, source_text, "
                    "target_text, priority, category_id, domain, category, scope_type, scope_id) "
                    "VALUES (?, ?, ?, ?, COALESCE(?, 0), ?, ?, ?, ?, ?)"
                ),
                (
                    entry.get("source_lang"),
                    entry.get("target_lang"),
                    entry_source,
                    entry_target,
                    entry.get("priority", 0),
                    entry.get("category_id"),
                    entry.get("domain"),
                    entry.get("category"),
                    entry.get("scope_type") or "project",
                    entry.get("scope_id") or "default",
                ),
            )
            print(f"Glossary upserted by unique constraints: {entry_source}")
        conn.commit()

    # Sync to terms center
    try:
        lang_code = entry.get("target_lang", "zh-TW")
        term_repo.sync_from_external(
            entry_source,
            category_name=entry.get("category_name"),
            source="reference",
            languages=[{"lang_code": lang_code, "value": entry_target}],
        )
    except Exception as e:
        print(f"Sync to terms center failed: {e}")


def batch_upsert_glossary(entries: list[dict]) -> None:
    if not entries:
        return
    _ensure_db()
    preserve_terms = _get_preserve_terms()
    with sqlite3.connect(DB_PATH) as conn:
        for entry in entries:
            entry_source = _normalize_glossary_text(entry.get("source_text", ""))
            entry_target = _normalize_glossary_text(entry.get("target_text", ""))
            if _is_preserve_term(entry_source, preserve_terms):
                continue
            conn.execute(
                (
                    "DELETE FROM glossary "
                    "WHERE source_lang = ? AND target_lang = ? "
                    "AND source_text = ?"
                ),
                (
                    entry.get("source_lang"),
                    entry.get("target_lang"),
                    entry_source,
                ),
            )
            conn.execute(
                (
                    "INSERT INTO glossary "
                    "(source_lang, target_lang, source_text, "
                    "target_text, priority, category_id, domain, category, scope_type, scope_id) "
                    "VALUES (?, ?, ?, ?, COALESCE(?, 0), ?, ?, ?, ?, ?)"
                ),
                (
                    entry.get("source_lang"),
                    entry.get("target_lang"),
                    entry_source,
                    entry_target,
                    entry.get("priority", 0),
                    entry.get("category_id"),
                    entry.get("domain"),
                    entry.get("category"),
                    entry.get("scope_type") or "project",
                    entry.get("scope_id") or "default",
                ),
            )
        conn.commit()

    # Sync to terms center
    for entry in entries:
        try:
            entry_source = _normalize_glossary_text(entry.get("source_text", ""))
            entry_target = _normalize_glossary_text(entry.get("target_text", ""))
            lang_code = entry.get("target_lang", "zh-TW")
            term_repo.sync_from_external(
                entry_source,
                category_name=entry.get("category_name"),
                source="reference",
                languages=[{"lang_code": lang_code, "value": entry_target}],
            )
        except Exception as e:
            print(f"Sync to terms center failed for {entry.get('source_text')}: {e}")


def clear_glossary() -> int:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("DELETE FROM glossary")
        conn.commit()
        return cur.rowcount


def delete_glossary(entry_id: int) -> int:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        # Get term text for sync
        row = conn.execute("SELECT source_text FROM glossary WHERE id = ?", (entry_id,)).fetchone()
        source_text = row[0] if row else None

        cur = conn.execute(
            "DELETE FROM glossary WHERE id = ?",
            (entry_id,),
        )
        conn.commit()

        # Sync to terms center
        if source_text:
            try:
                term_repo.delete_by_term(source_text)
            except Exception as e:
                print(f"Sync delete to terms center failed: {e}")

        return cur.rowcount


def batch_delete_glossary(ids: list[int]) -> int:
    if not ids:
        return 0
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        # Use executemany for efficiency
        cur = conn.executemany(
            "DELETE FROM glossary WHERE id = ?",
            [(entry_id,) for entry_id in ids],
        )
        conn.commit()
        return cur.rowcount
