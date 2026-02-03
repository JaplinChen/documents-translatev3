from __future__ import annotations

from pathlib import Path

from backend.services.preserve_terms_repository import list_preserve_terms

from .db import DB_PATH

_PRESERVE_TERMS_CACHE: list[dict] = []
_PRESERVE_TERMS_MTIME: float | None = None


def _load_preserve_terms() -> tuple[list[dict], float | None]:
    db_path = Path("data/translation_memory.db")
    try:
        mtime = db_path.stat().st_mtime if db_path.exists() else None
    except Exception:
        mtime = None
    try:
        terms = list_preserve_terms()
    except Exception:
        terms = []
    return terms, mtime


def _get_preserve_terms() -> list[dict]:
    global _PRESERVE_TERMS_CACHE, _PRESERVE_TERMS_MTIME
    terms, mtime = _load_preserve_terms()
    if mtime is None:
        _PRESERVE_TERMS_CACHE = []
        _PRESERVE_TERMS_MTIME = None
        return _PRESERVE_TERMS_CACHE
    if _PRESERVE_TERMS_MTIME != mtime:
        _PRESERVE_TERMS_CACHE = terms
        _PRESERVE_TERMS_MTIME = mtime
    return _PRESERVE_TERMS_CACHE


def _is_preserve_term(text: str, terms: list[dict]) -> bool:
    if not text:
        return False
    text_clean = text.strip()
    if not text_clean:
        return False
    for term_entry in terms:
        term = (term_entry.get("term") or "").strip()
        if not term:
            continue
        case_sensitive = term_entry.get("case_sensitive", True)
        if case_sensitive:
            if text_clean == term:
                return True
        else:
            if text_clean.lower() == term.lower():
                return True
    return False
