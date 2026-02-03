from __future__ import annotations

import logging

from backend.services.translation_memory_adapter import (
    get_glossary_terms,
    get_glossary_terms_any,
    get_tm_terms,
    get_tm_terms_any,
)

LOGGER = logging.getLogger(__name__)

_UNIFIED_TERMS_CACHE: list[dict] | None = None
_UNIFIED_TERMS_MTIME: float = 0


def load_preferred_terms(
    source_lang: str, target_language: str, use_tm: bool
) -> list[tuple[str, str]]:
    """Load glossary/TM-based preferred terms for the request."""
    if source_lang and source_lang != "auto":
        preferred_terms = get_glossary_terms(source_lang, target_language)
        if use_tm:
            preferred_terms.extend(get_tm_terms(source_lang, target_language))
    else:
        preferred_terms = get_glossary_terms_any(target_language)
        if use_tm:
            preferred_terms.extend(get_tm_terms_any(target_language))

    try:
        from backend.services.term_repository import list_terms, DB_PATH

        global _UNIFIED_TERMS_CACHE, _UNIFIED_TERMS_MTIME

        try:
            current_mtime = DB_PATH.stat().st_mtime if DB_PATH.exists() else 0
        except Exception:
            current_mtime = 0

        if _UNIFIED_TERMS_CACHE is None or current_mtime > _UNIFIED_TERMS_MTIME:
            _UNIFIED_TERMS_CACHE = list_terms({"status": "active"})
            _UNIFIED_TERMS_MTIME = current_mtime

        for term in _UNIFIED_TERMS_CACHE:
            source_text = term.get("term", "").strip()
            if not source_text:
                continue
            langs = term.get("languages", [])
            target_text = None
            for item in langs:
                if item.get("lang_code") == target_language:
                    target_text = item.get("value")
                    break

            if target_text:
                preferred_terms.append((source_text, target_text))
    except Exception as exc:
        LOGGER.error("Failed to load preferred terms from unified center: %s", exc)

    return preferred_terms
