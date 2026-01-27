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


def cache_key(block: dict, context: dict | None = None) -> str:
    """Generate a cache key based on text and optional LLM context."""
    text = block.get("source_text", "").strip()
    if not text:
        return ""
    if not context:
        return text

    # Context-aware hashing: if user changes model or tone, cache should be different
    # Focus on parameters that meaningfully change the translation output
    ctx_str = "|".join(
        [
            str(context.get("provider", "")),
            str(context.get("model", "")),
            str(context.get("tone", "")),
            str(context.get("vision_context", True)),
        ]
    )
    import hashlib

    # We use a combined hash to prevent key collisions and keep keys compact
    payload = f"{text}||{ctx_str}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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
