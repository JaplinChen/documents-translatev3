from __future__ import annotations

import json
import sqlite3

from .db import _normalize_text


def _fetch_languages(conn: sqlite3.Connection, term_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT lang_code, value FROM term_languages WHERE term_id = ?",
        (term_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _fetch_aliases(conn: sqlite3.Connection, term_id: int) -> list[str]:
    rows = conn.execute(
        "SELECT alias FROM term_aliases WHERE term_id = ?",
        (term_id,),
    ).fetchall()
    return [row["alias"] for row in rows]


def _fetch_term_full(conn: sqlite3.Connection, term_id: int) -> dict:
    term_row = conn.execute(
        (
            "SELECT t.*, c.name AS category_name "
            "FROM terms t "
            "LEFT JOIN categories c ON c.id = t.category_id "
            "WHERE t.id = ?"
        ),
        (term_id,),
    ).fetchone()
    if not term_row:
        return {}
    term = dict(term_row)
    term["languages"] = _fetch_languages(conn, term_id)
    term["aliases"] = _fetch_aliases(conn, term_id)
    return term


def _record_version(
    conn: sqlite3.Connection,
    term_id: int,
    before: dict | None,
    after: dict | None,
    created_by: str | None,
) -> None:
    payload = {"before": before, "after": after}
    conn.execute(
        ("INSERT INTO term_versions (term_id, diff, created_by) VALUES (?, ?, ?)"),
        (term_id, json.dumps(payload, ensure_ascii=False), created_by),
    )


def _upsert_languages(conn: sqlite3.Connection, term_id: int, languages: list[dict]) -> None:
    conn.execute("DELETE FROM term_languages WHERE term_id = ?", (term_id,))
    for lang in languages:
        lang_code = _normalize_text(lang.get("lang_code"))
        value = _normalize_text(lang.get("value"))
        if not lang_code:
            continue
        value_norm = value.lower() if value else ""
        conn.execute(
            (
                "INSERT INTO term_languages (term_id, lang_code, value, value_norm) "
                "VALUES (?, ?, ?, ?)"
            ),
            (term_id, lang_code, value, value_norm),
        )


def _replace_aliases(conn: sqlite3.Connection, term_id: int, aliases: list[str]) -> None:
    conn.execute("DELETE FROM term_aliases WHERE term_id = ?", (term_id,))
    for alias in aliases:
        alias_clean = _normalize_text(alias)
        if not alias_clean:
            continue
        alias_norm = alias_clean.lower()
        conn.execute(
            ("INSERT INTO term_aliases (term_id, alias, alias_norm) VALUES (?, ?, ?)"),
            (term_id, alias_clean, alias_norm),
        )
