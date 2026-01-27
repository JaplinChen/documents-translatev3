from __future__ import annotations

import re

def apply_placeholders(
    text: str,
    terms: list[tuple[str, str]],
) -> tuple[str, dict[str, str]]:
    if not text or not terms:
        return text, {}
    term_map = {}
    updated = text
    sorted_terms = sorted(terms, key=lambda item: len(item[0]), reverse=True)
    for idx, (source, target) in enumerate(sorted_terms):
        if not source:
            continue
        token = f"__TERM_{idx}__"
        pattern = re.compile(re.escape(source), re.IGNORECASE)
        if pattern.search(updated):
            updated = pattern.sub(token, updated)
            term_map[token] = target
    return updated, term_map


def restore_placeholders(text: str, mapping: dict[str, str]) -> str:
    if not text or not mapping:
        return text
    updated = text
    for token, target in mapping.items():
        updated = updated.replace(token, target)
    return updated


def has_placeholder(text: str) -> bool:
    return "__TERM_" in text
