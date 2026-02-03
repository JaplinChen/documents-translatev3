from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

from backend.services.llm_context import build_context
from backend.services.translate_chunk import prepare_chunk, translate_chunk_async
from backend.services.translate_retry import apply_translation_results

LOGGER = logging.getLogger(__name__)


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
        completed_ids = [b.get("client_id") for _, b in chunk if b.get("client_id")]
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
