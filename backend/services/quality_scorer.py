"""
Translation Quality Scorer Service

Evaluates translation quality based on multiple metrics.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

@dataclass
class QualityScore:
    """Translation quality assessment result."""

    overall_score: int  # 1-10
    length_ratio: float  # translated/source length ratio
    length_warning: str | None  # Warning if ratio is unusual
    has_untranslated: bool  # Source text appears in translation
    confidence_level: str  # "high", "medium", "low"
    issues: list[str]  # List of detected issues


def calculate_length_ratio(
    source: str,
    translated: str,
) -> tuple[float, str | None]:
    """Calculate length ratio and determine if it's acceptable."""
    if not source or not translated:
        return 1.0, None

    source_len = len(source.strip())
    trans_len = len(translated.strip())

    if source_len == 0:
        return 1.0, None

    ratio = trans_len / source_len

    warning = None
    if ratio < 0.5:
        warning = "譯文過短（可能遺漏內容）"
    elif ratio > 2.5:
        warning = "譯文過長（可能過度添加）"
    elif ratio < 0.7:
        warning = "譯文偏短"
    elif ratio > 1.8:
        warning = "譯文偏長"

    return round(ratio, 2), warning


def detect_untranslated(
    source: str,
    translated: str,
    source_lang: str = "vi",
) -> bool:
    """Detect if significant source text appears unchanged in translation."""
    if not source or not translated:
        return False

    # Extract words from source (excluding common technical terms)
    source_words = set(re.findall(r"\b[a-zA-ZÀ-ỹ]{4,}\b", source.lower()))
    trans_words = set(re.findall(r"\b[a-zA-ZÀ-ỹ]{4,}\b", translated.lower()))

    # Ignore common English technical terms
    technical_terms = {
        "database",
        "api",
        "http",
        "https",
        "json",
        "xml",
        "html",
        "css",
        "javascript",
        "python",
        "react",
        "vue",
        "notion",
        "obsidian",
        "wiki",
        "email",
        "cloud",
        "server",
        "client",
        "user",
        "admin",
        "login",
        "logout",
    }

    source_words -= technical_terms
    trans_words -= technical_terms

    # Check overlap
    overlap = source_words & trans_words

    if len(source_words) > 0:
        overlap_ratio = len(overlap) / len(source_words)
        # More than 30% overlap suggests untranslated content.
        return overlap_ratio > 0.3

    return False


def score_translation(
    source: str,
    translated: str,
    source_lang: str = "vi",
    target_lang: str = "zh-TW",
) -> QualityScore:
    """
    Score a translation based on multiple quality metrics.

    Returns a QualityScore with:
    - overall_score: 1-10 (10 = excellent)
    - length_ratio: translated/source length
    - length_warning: Warning if ratio is unusual
    - has_untranslated: True if source text appears in translation
    - confidence_level: "high", "medium", or "low"
    - issues: List of detected issues
    """
    issues = []
    score = 10

    # Check for empty translation
    if not translated or not translated.strip():
        return QualityScore(
            overall_score=1,
            length_ratio=0.0,
            length_warning="譯文為空",
            has_untranslated=False,
            confidence_level="low",
            issues=["譯文為空"],
        )

    # 1. Length ratio analysis
    length_ratio, length_warning = calculate_length_ratio(source, translated)
    if length_warning:
        issues.append(length_warning)
        if "過短" in length_warning or "過長" in length_warning:
            score -= 3
        else:
            score -= 1

    # 2. Untranslated content detection
    has_untranslated = detect_untranslated(source, translated, source_lang)
    if has_untranslated:
        issues.append("可能含有未翻譯內容")
        score -= 2

    # 3. Check for placeholder patterns
    placeholder_patterns = [
        r"\[.*?\]",  # [placeholder]
        r"\{.*?\}",  # {placeholder}
        r"TODO",
        r"FIXME",
        r"XXX",
    ]
    for pattern in placeholder_patterns:
        if re.search(pattern, translated, re.IGNORECASE):
            issues.append("包含佔位符或待辦標記")
            score -= 2
            break

    # 4. Check for excessive punctuation
    punct_count = len(re.findall(r"[!?！？]{2,}", translated))
    if punct_count > 0:
        issues.append("過多重複標點")
        score -= 1

    # 5. Determine confidence level
    if score >= 8:
        confidence = "high"
    elif score >= 5:
        confidence = "medium"
    else:
        confidence = "low"

    # Ensure score is within bounds
    score = max(1, min(10, score))

    return QualityScore(
        overall_score=score,
        length_ratio=length_ratio,
        length_warning=length_warning,
        has_untranslated=has_untranslated,
        confidence_level=confidence,
        issues=issues,
    )


def get_score_color(score: int) -> str:
    """Get color class for score display."""
    if score >= 8:
        return "success"  # Green
    elif score >= 5:
        return "warning"  # Yellow/Orange
    else:
        return "danger"  # Red
