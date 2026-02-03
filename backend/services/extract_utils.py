from __future__ import annotations

import re
from pathlib import Path

from langdetect import DetectorFactory, detect
from backend.services.preserve_terms_repository import list_preserve_terms
from backend.services.language_detect import _VI_DIACRITIC_RE

# Set seed for consistent langdetect results
DetectorFactory.seed = 0


_PRESERVE_TERMS_CACHE: list[dict] = []
_PRESERVE_TERMS_MTIME: float | None = None


def _load_preserve_terms() -> tuple[list[dict], float | None]:
    """Load preserve terms from SQLite table."""
    from backend.services.preserve_terms_repository import list_preserve_terms

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
    """Return preserve terms with simple mtime-based cache invalidation."""
    global _PRESERVE_TERMS_CACHE, _PRESERVE_TERMS_MTIME
    db_path = Path("data/translation_memory.db")
    try:
        current_mtime = db_path.stat().st_mtime if db_path.exists() else None
    except Exception:
        current_mtime = None

    if _PRESERVE_TERMS_MTIME != current_mtime or not _PRESERVE_TERMS_CACHE:
        terms, mtime = _load_preserve_terms()
        _PRESERVE_TERMS_CACHE = terms
        _PRESERVE_TERMS_MTIME = mtime

    return _PRESERVE_TERMS_CACHE


def is_exact_term_match(text: str) -> bool:
    """Check if text exactly matches a preserve term. Skip extraction if it does."""
    if not text:
        return False
    text_clean = text.strip()
    if not text_clean:
        return False

    for term_entry in _get_preserve_terms():
        term = term_entry.get("term", "")
        case_sensitive = term_entry.get("case_sensitive", True)
        if case_sensitive:
            if text_clean == term:
                return True
        else:
            if text_clean.lower() == term.lower():
                return True
    return False


def is_numeric_only(text: str) -> bool:
    """Check if text is only numbers, punctuation, or whitespace."""
    if not text or not text.strip():
        return True
    # If it contains any letter (Unicode alpha), it's not numeric-only.
    if any(ch.isalpha() for ch in text):
        return False
    return True


def is_technical_terms_only(text: str) -> bool:  # noqa: C901
    """
    Check if the text consists only of technical terms, product names,
    or acronyms.
    First checks preserve_terms, then falls back to auto-detection.
    """
    if not text or not text.strip():
        return True

    # Priority 1: Check preserve terms database
    text_clean = text.strip()
    for term_entry in _get_preserve_terms():
        term = term_entry.get("term", "")
        case_sensitive = term_entry.get("case_sensitive", True)

        if case_sensitive:
            if text_clean == term:
                return True
        else:
            if text_clean.lower() == term.lower():
                return True

    # Priority 2: Auto-detection fallback
    text_clean = text.strip()

    # Skip common IT prefixes (Check before normalization to preserve slashes/dots)
    SKIP_PREFIXES = (
        r"^(ID|UUID|SN|PN|IP|MAC|No|No\.|S/N|P/N|ID\s+No|Item\s+No|Part\s+No|Serial\s+No)[:：\s]"
    )
    if re.search(SKIP_PREFIXES, text_clean, re.IGNORECASE):
        return True

    # Remove common separators for further word-level checks
    cleaned = re.sub(r"[,、，/\s]+", " ", text_clean).strip()

    if _VI_DIACRITIC_RE.search(text_clean):
        return False

    # If contains any CJK characters or Thai, it's not pure technical terms.
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
    # 1. Employee ID or code patterns: #00661, ABC-1234, ID-999, etc.
    is_all_caps_or_id = all(
        (re.match(r"^[#A-Z0-9_\-]+$", w) or re.match(r"^#\d+$", w)) and len(w) <= 30 for w in words
    )
    # 2. MixedCase words (CamelCase)
    is_mixed_case = all(re.match(r"^[A-Z][a-z]*[A-Z][a-zA-Z]*$", w) and len(w) <= 30 for w in words)
    # 3. MAC address pattern
    is_mac = any(re.match(r"^[0-9A-F]{2}([:\-][0-9A-F]{2}){5}$", w, re.IGNORECASE) for w in words)
    # 4. IP address pattern
    is_ip = any(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", w) for w in words)
    # 5. Version strings (e.g., v1.0.2)
    is_version = any(re.match(r"^v?\d+(\.\d+){1,3}$", w, re.IGNORECASE) for w in words)

    if is_all_caps_or_id or is_mixed_case or is_mac or is_ip or is_version:
        return True

    is_title_case = all(re.match(r"^[A-Z][a-z]+$", w) for w in words)
    is_pure_lower = all(re.match(r"^[a-z]+$", w) for w in words)

    # TitleCase or pure lower is only filtered if very short (<= 3 chars)
    if (is_title_case or is_pure_lower) and word_count <= 1 and len(cleaned) <= 3:
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
