from __future__ import annotations

from backend.services.llm_placeholders import has_placeholder
from backend.services.llm_utils import cache_key, tm_respects_terms
from backend.services.translation_memory_adapter import lookup_tm


def _check_local_cache(
    key: str,
    translated_texts: list[str | None],
    index: int,
    local_cache: dict[str, str],
    use_placeholders: bool,
) -> bool:
    cached = local_cache.get(key)
    if not cached:
        return False
    if not use_placeholders and has_placeholder(cached):
        return False
    translated_texts[index] = cached
    return True


def _check_tm(
    block: dict,
    key: str,
    target_language: str,
    source_lang: str,
    preferred_terms: list[tuple[str, str]],
    translated_texts: list[str | None],
    local_cache: dict[str, str],
    use_placeholders: bool,
    llm_context: dict | None,
    index: int,
) -> bool:
    tm_hit = lookup_tm(
        source_lang=source_lang,
        target_lang=target_language,
        text=block.get("source_text", "").strip(),
        context=llm_context,
        use_fuzzy=True,
    )
    if (
        tm_hit
        and tm_respects_terms(key, tm_hit, preferred_terms)
        and (use_placeholders or not has_placeholder(tm_hit))
    ):
        translated_texts[index] = tm_hit
        local_cache[key] = tm_hit
        return True
    return False


def prepare_pending_blocks(
    blocks_list: list[dict],
    target_language: str,
    source_lang: str,
    use_tm: bool,
    use_placeholders: bool,
    preferred_terms: list[tuple[str, str]],
    refresh: bool = False,
    llm_context: dict | None = None,
) -> tuple[list[str | None], list[tuple[int, dict]], dict[str, str]]:
    """Prepare warm cache of translated texts and pending blocks."""
    local_cache: dict[str, str] = {}
    translated_texts: list[str | None] = [None] * len(blocks_list)
    pending: list[tuple[int, dict]] = []

    for index, block in enumerate(blocks_list):
        key = cache_key(block, context=llm_context)
        if not key:
            translated_texts[index] = ""
            continue

        if not refresh and _check_local_cache(
            key, translated_texts, index, local_cache, use_placeholders
        ):
            continue

        if (
            not refresh
            and source_lang
            and source_lang != "auto"
            and use_tm
            and _check_tm(
                block,
                key,
                target_language,
                source_lang,
                preferred_terms,
                translated_texts,
                local_cache,
                use_placeholders,
                llm_context,
                index,
            )
        ):
            continue

        pending.append((index, block))

    return translated_texts, pending, local_cache
