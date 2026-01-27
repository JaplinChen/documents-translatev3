from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

from backend.services.llm_context import build_context
from backend.services.llm_placeholders import has_placeholder
from backend.services.llm_utils import (
    cache_key,
    tm_respects_terms,
)
from backend.services.translate_chunk import (
    prepare_chunk,
    translate_chunk_async,
)
from backend.services.translate_retry import apply_translation_results
from backend.services.translation_memory import (
    get_glossary_terms,
    get_glossary_terms_any,
    get_tm_terms,
    get_tm_terms_any,
    lookup_tm,
)

LOGGER = logging.getLogger(__name__)


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

    LOGGER.debug(
        "prepare_pending_blocks start blocks=%s refresh=%s use_tm=%s",
        len(blocks_list),
        refresh,
        use_tm,
    )

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


def load_preferred_terms(
    source_lang: str, target_language: str, use_tm: bool
) -> list[tuple[str, str]]:
    """Load glossary/TM-based preferred terms for the request."""
    if source_lang and source_lang != "auto":
        preferred_terms = get_glossary_terms(source_lang, target_language)
        if use_tm:
            preferred_terms.extend(get_tm_terms(source_lang, target_language))
    else:
        preferred_terms = get_glossary_terms_any(target_language)
        if use_tm:
            preferred_terms.extend(get_tm_terms_any(target_language))
    return preferred_terms


async def process_chunk_async(
    translator,
    provider,
    chunk,
    chunk_blocks,
    placeholder_maps,
    target_language,
    context,
    preferred_terms,
    placeholder_tokens,
    tone,
    vision_context,
    params,
    chunk_index,
    fallback_on_error,
    mode,
    translated_texts,
    local_cache,
    glossary,
    use_tm,
    on_progress: Callable[[dict], Any] | None = None,
    llm_context: dict | None = None,
):
    """Helper to process a single chunk asynchronously."""
    chunk_started = time.perf_counter()

    if params.get("chunk_delay", 0) > 0:
        await asyncio.sleep(params["chunk_delay"] * (chunk_index - 1))

    result = await translate_chunk_async(
        translator,
        provider,
        chunk_blocks,
        target_language,
        context,
        preferred_terms,
        placeholder_tokens,
        tone,
        vision_context,
        params,
        chunk_index,
        fallback_on_error,
        mode,
    )

    apply_translation_results(
        chunk,
        placeholder_maps,
        result,
        translated_texts,
        local_cache,
        glossary,
        target_language,
        use_tm,
        llm_context=llm_context,
    )

    if on_progress:
        completed_indices = [idx for idx, _ in chunk]
        completed_ids = [
            b.get("client_id")
            for _, b in chunk
            if b.get("client_id")
        ]
        completed_blocks = []
        for idx, block in chunk:
            client_id = block.get("client_id")
            translated_text = translated_texts[idx]
            if translated_text is None:
                continue
            completed_blocks.append(
                {
                    "client_id": client_id,
                    "translated_text": translated_text,
                }
            )
        try:
            val = on_progress(
                {
                    "chunk_index": chunk_index,
                    "completed_indices": completed_indices,
                    "completed_ids": completed_ids,
                    "completed_blocks": completed_blocks,
                    "chunk_size": len(chunk),
                    "total_pending": len(translated_texts),
                    "timestamp": time.time(),
                }
            )
            if asyncio.iscoroutine(val):
                await val
        except Exception:
            LOGGER.exception("Error in progress callback")

    chunk_duration = time.perf_counter() - chunk_started
    LOGGER.info(
        "LLM chunk %s completed in %.2fs (async)",
        chunk_index,
        chunk_duration,
    )


def create_async_chunk_tasks(
    chunk_list,
    translator,
    provider,
    blocks_list,
    target_language,
    preferred_terms,
    use_placeholders,
    params,
    fallback_on_error,
    mode,
    translated_texts,
    local_cache,
    glossary,
    use_tm,
    tone,
    vision_context,
    on_progress,
    llm_context: dict | None = None,
):
    """Create async tasks for processing chunks."""
    tasks = []
    for chunk_index, chunk in enumerate(chunk_list, start=1):
        chunk_blocks, placeholder_maps, placeholder_tokens = prepare_chunk(
            chunk, use_placeholders, preferred_terms
        )
        context = build_context(
            params["context_strategy"],
            blocks_list,
            chunk_blocks,
        )

        tasks.append(
            process_chunk_async(
                translator,
                provider,
                chunk,
                chunk_blocks,
                placeholder_maps,
                target_language,
                context,
                preferred_terms,
                placeholder_tokens,
                tone,
                vision_context,
                params,
                chunk_index,
                fallback_on_error,
                mode,
                translated_texts,
                local_cache,
                glossary,
                use_tm,
                on_progress,
                llm_context=llm_context,
            )
        )
    return tasks
