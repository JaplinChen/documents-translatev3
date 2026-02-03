from __future__ import annotations

from .db import _connect, _ensure_db, _normalize_text
from .helpers import _fetch_languages
from .terms_write import create_term, update_term, delete_term


def sync_from_external(
    term: str,
    category_name: str | None = None,
    source: str = "manual",
    languages: list[dict] | None = None,
    created_by: str | None = None,
    filename: str | None = None,
    source_lang: str | None = None,
    target_lang: str | None = None,
    priority: int | None = None,
    case_rule: str | None = None,
) -> dict:
    """Sync a term from an external source. Merges languages if the term exists."""
    _ensure_db()
    term_text = _normalize_text(term)
    if not term_text:
        return {}

    term_norm = term_text.lower()
    with _connect() as conn:
        row = conn.execute("SELECT id FROM terms WHERE term_norm = ?", (term_norm,)).fetchone()
        term_id = int(row["id"]) if row else None

    if term_id:
        with _connect() as conn:
            current_langs = _fetch_languages(conn, term_id)
            lang_dict = {l["lang_code"]: l["value"] for l in current_langs}
            for lang in languages or []:
                if lang.get("value"):
                    lang_dict[lang["lang_code"]] = lang["value"]

            merged_languages = [{"lang_code": k, "value": v} for k, v in lang_dict.items()]

            payload = {
                "term": term_text,
                "category_name": category_name,
                "source": source,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "priority": priority,
                "case_rule": case_rule,
                "filename": filename,
                "languages": merged_languages,
                "status": "active",
                "created_by": created_by,
            }
            return update_term(term_id, payload)
    payload = {
        "term": term_text,
        "category_name": category_name,
        "source": source,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "priority": priority,
        "case_rule": case_rule,
        "filename": filename,
        "languages": languages or [],
        "status": "active",
        "created_by": created_by,
        "allow_create_category": True,
    }
    return create_term(payload)


def delete_by_term(term: str) -> None:
    """Delete a term by its text (e.g. from sync hooks)."""
    _ensure_db()
    term_norm = _normalize_text(term).lower()
    with _connect() as conn:
        row = conn.execute("SELECT id FROM terms WHERE term_norm = ?", (term_norm,)).fetchone()
        if row:
            delete_term(int(row["id"]))


def upsert_term_by_norm(payload: dict) -> dict:
    _ensure_db()
    term = _normalize_text(payload.get("term"))
    if not term:
        raise ValueError("術語不可為空")
    term_norm = term.lower()
    with _connect() as conn:
        row = conn.execute(
            "SELECT id FROM terms WHERE term_norm = ?",
            (term_norm,),
        ).fetchone()
    if row:
        return update_term(int(row["id"]), payload)
    return create_term(payload)
