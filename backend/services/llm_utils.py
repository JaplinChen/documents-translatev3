from __future__ import annotations

import json
from collections.abc import Iterable


def safe_json_loads(content: str) -> dict:
    if not content:
        raise ValueError("Empty LLM response content")
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(content[start : end + 1])
        raise ValueError("LLM response is not valid JSON")


def cache_key(block: dict) -> str:
    return block.get("source_text", "").strip()


def chunked(items: list[tuple[int, dict]], size: int) -> Iterable[list[tuple[int, dict]]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def tm_respects_terms(
    source_text: str, translated_text: str, preferred_terms: list[tuple[str, str]]
) -> bool:
    if not source_text or not translated_text or not preferred_terms:
        return True
    for source, target in preferred_terms:
        if not source or not target:
            continue
        if source.lower() in source_text.lower() and target not in translated_text:
            return False
    return True
