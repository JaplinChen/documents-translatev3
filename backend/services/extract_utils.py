from __future__ import annotations

import json
import re
from pathlib import Path


def _load_preserve_terms() -> list[dict]:
    """Load preserve terms from JSON file."""
    # Try multiple possible locations for preserve_terms.json
    base_path = Path(__file__).parent.parent
    possible_paths = [
        base_path / "data" / "preserve_terms.json",
        base_path / "services" / "data" / "preserve_terms.json",
    ]
    
    for preserve_file in possible_paths:
        if preserve_file.exists():
            try:
                with open(preserve_file, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                continue
    return []


PRESERVE_TERMS = _load_preserve_terms()


def is_numeric_only(text: str) -> bool:
    """Check if the text consists only of numbers, punctuation, or whitespace."""
    if not text or not text.strip():
        return True
    # If it contains any letter (English, CJK), it's not purely numeric/symbolic
    if re.search(r"[a-zA-Z\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]", text):
        return False
    return True


def is_technical_terms_only(text: str) -> bool:
    """
    Check if the text consists only of technical terms, product names, or acronyms.
    First checks against preserve_terms.json database, then falls back to auto-detection.
    """
    if not text or not text.strip():
        return True

    # Priority 1: Check preserve terms database
    text_clean = text.strip()
    for term_entry in PRESERVE_TERMS:
        term = term_entry.get("term", "")
        case_sensitive = term_entry.get("case_sensitive", True)

        if case_sensitive:
            if text_clean == term:
                return True
        else:
            if text_clean.lower() == term.lower():
                return True

    # Priority 2: Auto-detection fallback
    # Remove common separators
    cleaned = re.sub(r"[,、，/\s]+", " ", text).strip()

    # Check if contains any CJK characters (if yes, it's not pure technical terms)
    if re.search(r"[\u4e00-\u9fff\u3040-\u30ff\u0e00-\u0e7f]", cleaned):
        return False

    # Check if contains sentence-forming words (articles, prepositions, verbs)
    sentence_indicators = (
        r"\b(the|a|an|is|are|was|were|be|have|has|had|do|does|did|will|would|can|could|should|"
        r"may|might|must|please|this|that|these|those|with|from|to|in|on|at|for|of|and|or|but)\b"
    )
    if re.search(sentence_indicators, cleaned, re.IGNORECASE):
        return False

    # Split into words
    words = cleaned.split()
    word_count = len(words)

    # Heuristic: True technical term lists are usually short (1-3 words) 
    if word_count > 10:
        return False
        
    # Patterns: 
    is_all_caps = all(re.match(r"^[A-Z0-9_\-]+$", w) for w in words)
    is_mixed_case = all(re.match(r"^[A-Z][a-z]*[A-Z][a-zA-Z]*$", w) for w in words)
    is_title_case = all(re.match(r"^[A-Z][a-z]+$", w) for w in words)
    is_pure_lower = all(re.match(r"^[a-z]+$", w) for w in words)

    if is_all_caps or is_mixed_case:
        return True
    
    # TitleCase or pure lower is only filtered if very short
    if (is_title_case or is_pure_lower) and word_count <= 1:
        return True

    return False
