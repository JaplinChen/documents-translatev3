"""
Smart Term Suggester Service.

Analyzes text to suggest preserve terms or glossary entries.
Uses NLP patterns to identify technical terms and acronyms.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

@dataclass
class TermSuggestion:
    """A suggested term with metadata."""

    term: str
    category: str  # "product", "acronym", "technical", "proper_noun"
    confidence: float  # 0.0 - 1.0
    context: str  # Where the term was found
    suggested_action: str  # "preserve" or "translate"


# Patterns for detecting different term types
ACRONYM_PATTERN = re.compile(r"\b[A-Z]{2,6}\b")
PRODUCT_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b")  # CamelCase
TECH_PATTERNS = [
    re.compile(
        r"\b(?:API|SDK|HTTP|HTTPS|JSON|XML|SQL|CSS|HTML|JS|PDF|AI|ML|UI|UX)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b\w+(?:\.js|\.py|\.ts|\.jsx|\.tsx)\b"),  # File extensions
    re.compile(r"\b(?:v?\d+\.\d+(?:\.\d+)?)\b"),  # Version numbers
]

# Known product/brand names to preserve
KNOWN_PRODUCTS = {
    "notion",
    "obsidian",
    "excel",
    "powerpoint",
    "word",
    "google",
    "microsoft",
    "slack",
    "discord",
    "zoom",
    "github",
    "gitlab",
    "docker",
    "kubernetes",
    "react",
    "vue",
    "angular",
    "node",
    "python",
    "java",
    "typescript",
    "chatgpt",
    "gpt",
    "claude",
    "gemini",
    "ollama",
    "openai",
    "anthropic",
}


def extract_acronyms(text: str) -> list[TermSuggestion]:
    """Extract acronyms (2-6 uppercase letters)."""
    suggestions = []
    matches = ACRONYM_PATTERN.findall(text)

    for match in set(matches):
        # Skip very common words
        if match.lower() in {
            "am",
            "pm",
            "ok",
            "to",
            "in",
            "on",
            "at",
            "of",
            "it",
            "is",
        }:
            continue

        suggestions.append(
            TermSuggestion(
                term=match,
                category="acronym",
                confidence=0.8,
                context=_get_context(text, match),
                suggested_action="preserve",
            )
        )

    return suggestions


def extract_products(text: str) -> list[TermSuggestion]:
    """Extract product names (CamelCase or known brands)."""
    suggestions = []

    # CamelCase patterns
    camel_matches = PRODUCT_PATTERN.findall(text)
    for match in set(camel_matches):
        suggestions.append(
            TermSuggestion(
                term=match,
                category="product",
                confidence=0.7,
                context=_get_context(text, match),
                suggested_action="preserve",
            )
        )

    # Known products
    words = set(re.findall(r"\b\w+\b", text.lower()))
    for product in KNOWN_PRODUCTS & words:
        # Find original case in text
        original = re.search(rf"\b{product}\b", text, re.IGNORECASE)
        if original:
            suggestions.append(
                TermSuggestion(
                    term=original.group(),
                    category="product",
                    confidence=0.95,
                    context=_get_context(text, original.group()),
                    suggested_action="preserve",
                )
            )

    return suggestions


def extract_technical_terms(text: str) -> list[TermSuggestion]:
    """Extract technical terms and patterns."""
    suggestions = []

    for pattern in TECH_PATTERNS:
        matches = pattern.findall(text)
        for match in set(matches):
            suggestions.append(
                TermSuggestion(
                    term=match,
                    category="technical",
                    confidence=0.85,
                    context=_get_context(text, match),
                    suggested_action="preserve",
                )
            )

    return suggestions


def _get_context(text: str, term: str, window: int = 50) -> str:
    """Get surrounding context for a term."""
    idx = text.find(term)
    if idx == -1:
        return ""

    start = max(0, idx - window)
    end = min(len(text), idx + len(term) + window)

    context = text[start:end].strip()
    if start > 0:
        context = "..." + context
    if end < len(text):
        context = context + "..."

    return context


def suggest_terms(text: str) -> list[TermSuggestion]:
    """
    Analyze text and suggest terms for preservation or translation.

    Returns a deduplicated list of TermSuggestion objects sorted by confidence.
    """
    all_suggestions = []

    all_suggestions.extend(extract_acronyms(text))
    all_suggestions.extend(extract_products(text))
    all_suggestions.extend(extract_technical_terms(text))

    # Deduplicate by term (case-insensitive)
    seen = set()
    unique = []
    for s in all_suggestions:
        key = s.term.lower()
        if key not in seen:
            seen.add(key)
            unique.append(s)

    # Sort by confidence descending
    unique.sort(key=lambda x: x.confidence, reverse=True)

    return unique


def suggest_terms_for_blocks(blocks: list[dict]) -> list[TermSuggestion]:
    """Analyze all blocks and suggest terms."""
    combined_text = " ".join(b.get("original_text", "") for b in blocks)
    return suggest_terms(combined_text)
