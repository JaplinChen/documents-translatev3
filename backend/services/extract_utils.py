from __future__ import annotations

import json
import re
from pathlib import Path

from langdetect import DetectorFactory, detect

# Set seed for consistent langdetect results
DetectorFactory.seed = 0


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
    """Check if text is only numbers, punctuation, or whitespace."""
    if not text or not text.strip():
        return True
    # If it contains any letter (English, CJK), it's not numeric-only.
    if re.search(r"[a-zA-Z\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]", text):
        return False
    return True


def is_technical_terms_only(text: str) -> bool:  # noqa: C901
    """
    Check if the text consists only of technical terms, product names,
    or acronyms.
    First checks preserve_terms.json, then falls back to auto-detection.
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

    # If contains any CJK characters, it's not pure technical terms.
    if re.search(r"[\u4e00-\u9fff\u3040-\u30ff\u0e00-\u0e7f]", cleaned):
        return False

    # Check if contains sentence-forming words (articles, prepositions, verbs)
    sentence_indicators = (
        r"\b(the|a|an|is|are|was|were|be|have|has|had|do|does|did|"
        r"will|would|can|could|should|may|might|must|please|this|"
        r"that|these|those|with|from|to|in|on|at|for|of|and|or|but)\b"
    )
    if re.search(sentence_indicators, cleaned, re.IGNORECASE):
        return False

    # Split into words
    words = cleaned.split()
    word_count = len(words)

    # Heuristic: technical term lists are usually short (1-3 words).
    if word_count > 10:
        return False

    # Patterns:
    # Employee ID or code patterns: #00661, ABC-1234, ID-999, etc.
    is_all_caps_or_id = all(
        (
            re.match(r"^[#A-Z0-9_\-]+$", w)
            or re.match(r"^#\d+$", w)
        )
        and len(w) <= 30
        for w in words
    )
    is_mixed_case = all(
        re.match(r"^[A-Z][a-z]*[A-Z][a-zA-Z]*$", w) and len(w) <= 30
        for w in words
    )
    is_title_case = all(re.match(r"^[A-Z][a-z]+$", w) for w in words)
    is_pure_lower = all(re.match(r"^[a-z]+$", w) for w in words)

    if is_all_caps_or_id or is_mixed_case:
        return True

    # TitleCase or pure lower is only filtered if very short (<= 3 chars)
    if (
        (is_title_case or is_pure_lower)
        and word_count <= 1
        and len(cleaned) <= 3
    ):
        return True

    return False


def is_garbage_text(text: str) -> bool:
    """Detect text that looks like UUIDs, long hex, or code."""
    if not text or len(text.strip()) < 5:
        return False

    cleaned = text.strip()
    # UUID pattern
    if re.match(r"^[a-fA-F0-9\-]{32,}$", cleaned):
        return True

    # Hex pattern
    if re.match(r"^0x[a-fA-F0-9]+$", cleaned) and len(cleaned) > 10:
        return True

    # High entropy / Random character check
    if len(cleaned) > 20:
        alphas = sum(c.isalpha() for c in cleaned)
        if alphas / len(cleaned) < 0.2:  # Mostly symbols or numbers
            return True

    try:
        # Simple langdetect check to see if it's identifiable
        # Note: langdetect can be slow, so we only use it for longer strings
        if len(cleaned) > 50:
            lang = detect(cleaned)
            # If it's unidentifiable, detect() might throw or return 'und'.
            if lang == "und":
                return True
    except Exception:
        pass

    return False
