from __future__ import annotations

import json
import logging

from backend.services.term_repository import list_terms
from backend.services.translation_memory_adapter import get_glossary

from .constants import COMMON_TYPO_MAP

LOGGER = logging.getLogger(__name__)


def _suggest_typo_corrections(text: str) -> str:
    """針對文本進行初步的錯字建議註記，不直接修改原文，但提供提示。"""
    hints = []
    text_lower = text.lower()
    for typo, correction in COMMON_TYPO_MAP.items():
        if typo in text_lower:
            hints.append(f"注意：原文中的 '{typo}' 可能應為 '{correction}'。")
    return "\n".join(hints) if hints else ""


def _load_existing_terms(target_lang: str) -> list[str]:
    """
    Load existing terms from term repository and glossary to avoid duplicates.
    Returns a list of source text terms (lowercase) that already exist.
    """
    existing = set()

    try:
        terms = list_terms({"status": "active"})
        for term in terms:
            term_text = term.get("term", "").strip().lower()
            if term_text:
                existing.add(term_text)
    except Exception as exc:
        LOGGER.warning(f"Failed to load terms from repository: {exc}")

    try:
        glossary = get_glossary(limit=1000)
        for entry in glossary:
            source_text = entry.get("source_text", "").strip().lower()
            if source_text:
                existing.add(source_text)
    except Exception as exc:
        LOGGER.warning(f"Failed to load glossary entries: {exc}")

    return list(existing)


def _parse_json_array(content: str) -> list:
    """
    Parse JSON array from LLM response.
    Handles both raw JSON and markdown-wrapped JSON.
    """
    if not content or not content.strip():
        return []

    text = content.strip()

    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
        return []
    except json.JSONDecodeError:
        pass

    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            result = json.loads(text[start : end + 1])
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    return []
