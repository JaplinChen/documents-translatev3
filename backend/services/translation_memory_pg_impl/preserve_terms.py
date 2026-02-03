from __future__ import annotations

from backend.services.preserve_terms_repository import list_preserve_terms

_PRESERVE_TERMS_CACHE: list[dict] = []
_PRESERVE_TERMS_MTIME: float | None = None


def _load_preserve_terms() -> tuple[list[dict], float | None]:
    try:
        terms = list_preserve_terms()
    except Exception:
        terms = []
    return terms, None


def _get_preserve_terms() -> list[dict]:
    global _PRESERVE_TERMS_CACHE, _PRESERVE_TERMS_MTIME
    terms, _ = _load_preserve_terms()
    _PRESERVE_TERMS_CACHE = terms
    _PRESERVE_TERMS_MTIME = None
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
