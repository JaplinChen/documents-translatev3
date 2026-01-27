"""LLM-based translation service for PPTX text blocks.

This module provides the main translation orchestration logic,
delegating to sub-modules for configuration, prompts, and retry handling.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

import httpx

from backend.config import settings
from backend.services.llm_clients import MockTranslator
from backend.services.llm_context import build_context
from backend.services.llm_contract import build_contract
from backend.services.llm_glossary import load_glossary
from backend.services.llm_utils import chunked
from backend.services.bilingual_alignment import align_bilingual_blocks
from backend.services.translate_chunk import (
    prepare_chunk,
    translate_chunk,
    translate_chunk_async,
)
from backend.services.translate_llm_helpers import (
    create_async_chunk_tasks,
    load_preferred_terms,
    prepare_pending_blocks,
)
from backend.services.translate_retry import apply_translation_results
from backend.services.translate_selector import get_translation_params, select_translator

LOGGER = logging.getLogger(__name__)


def translate_blocks(
    blocks: list[dict],
    target_language: str,
    source_language: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    use_tm: bool = True,
    tone: str | None = None,
    vision_context: bool = True,
    smart_layout: bool = True,
    param_overrides: dict | None = None,
    mode: str | None = None,
) -> dict:
    """Translate text blocks using LLM (Synchronous)."""
    resolved_mode = (mode or settings.translate_llm_mode).lower()
    fallback_on_error = settings.llm_fallback_on_error

    if resolved_mode == "mock":
        resolved_provider = "mock"
        translator = MockTranslator()
    else:
        resolved_provider, translator = select_translator(
            provider, model, api_key, base_url, fallback_on_error
        )

    blocks_list = list(blocks)
    source_lang = source_language or settings.source_language

    # Apply alignment
    if resolved_mode != "mock":
        blocks_list = align_bilingual_blocks(blocks_list, source_lang, target_language)

    preferred_terms = load_preferred_terms(source_lang, target_language, use_tm)
    use_placeholders = resolved_provider != "ollama"

    param_overrides = (param_overrides or {}).copy()
    refresh = param_overrides.get("refresh", False)

    llm_context = {
        "provider": resolved_provider,
        "model": model,
        "tone": tone,
        "vision_context": vision_context,
    }

    translated_texts, pending, local_cache = prepare_pending_blocks(
        blocks_list,
        target_language,
        source_lang,
        use_tm,
        use_placeholders,
        preferred_terms,
        refresh=refresh,
        llm_context=llm_context,
    )

    param_overrides.update({"model": model, "tone": tone, "vision_context": vision_context})
    params = get_translation_params(resolved_provider, overrides=param_overrides)
    chunk_size = params["chunk_size"]
    if params["single_request"]:
        chunk_size = len(pending) if pending else chunk_size
        params["chunk_delay"] = 0.0

    glossary = load_glossary(params["glossary_path"])

    LOGGER.info(
        "LLM translate start provider=%s model=%s blocks=%s chunk=%s",
        resolved_provider,
        model or "",
        len(blocks_list),
        chunk_size,
    )

    for chunk_index, chunk in enumerate(chunked(pending, chunk_size), start=1):
        chunk_started = time.perf_counter()
        chunk_blocks, placeholder_maps, placeholder_tokens = prepare_chunk(
            chunk, use_placeholders, preferred_terms
        )
        context = build_context(params["context_strategy"], blocks_list, chunk_blocks)

        result = translate_chunk(
            translator,
            resolved_provider,
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
            resolved_mode,
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

        chunk_duration = time.perf_counter() - chunk_started
        LOGGER.info("LLM chunk %s completed in %.2fs", chunk_index, chunk_duration)
        if params["chunk_delay"]:
            time.sleep(params["chunk_delay"])

    final_texts = [text if text is not None else "" for text in translated_texts]

    # Result Migration Pass (Bilingual Alignment)
    for i, block in enumerate(blocks_list):
        if block.get("alignment_role") == "source":
            # For Source blocks in a pair, we show original text to prevent redundant output items
            final_texts[i] = block.get("source_text", "")

    return build_contract(
        blocks=blocks_list,
        translated_texts=final_texts,
        target_language=target_language,
    )


async def translate_blocks_async(
    blocks: list[dict],
    target_language: str,
    source_language: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    use_tm: bool = True,
    tone: str | None = None,
    vision_context: bool = True,
    smart_layout: bool = True,
    param_overrides: dict | None = None,
    on_progress: Callable[[dict], Any] | None = None,
    mode: str | None = None,
) -> dict:
    """Translate text blocks using LLM (Asynchronous)."""
    resolved_mode = (mode or settings.translate_llm_mode).lower()
    fallback_on_error = settings.llm_fallback_on_error

    if resolved_mode == "mock":
        resolved_provider = "mock"
        translator = MockTranslator()
    else:
        resolved_provider, translator = select_translator(
            provider, model, api_key, base_url, fallback_on_error
        )

    blocks_list = list(blocks)
    source_lang = source_language or settings.source_language

    # Apply alignment
    if resolved_mode != "mock":
        blocks_list = align_bilingual_blocks(blocks_list, source_lang, target_language)

    preferred_terms = load_preferred_terms(source_lang, target_language, use_tm)
    use_placeholders = resolved_provider != "ollama"

    param_overrides = (param_overrides or {}).copy()
    refresh = param_overrides.get("refresh", False)

    llm_context = {
        "provider": resolved_provider,
        "model": model,
        "tone": tone,
        "vision_context": vision_context,
    }

    translated_texts, pending, local_cache = prepare_pending_blocks(
        blocks_list,
        target_language,
        source_lang,
        use_tm,
        use_placeholders,
        preferred_terms,
        refresh=refresh,
        llm_context=llm_context,
    )

    param_overrides.update({"model": model, "tone": tone, "vision_context": vision_context})
    params = get_translation_params(resolved_provider, overrides=param_overrides)
    chunk_size = params["chunk_size"]
    if params["single_request"]:
        chunk_size = len(pending) if pending else chunk_size

    glossary = load_glossary(params["glossary_path"])

    LOGGER.info(
        "LLM translate start async provider=%s model=%s blocks=%s chunk=%s",
        resolved_provider,
        model or "",
        len(blocks_list),
        chunk_size,
    )

    chunk_list = list(chunked(pending, chunk_size))
    tasks = create_async_chunk_tasks(
        chunk_list,
        translator,
        resolved_provider,
        blocks_list,
        target_language,
        preferred_terms,
        use_placeholders,
        params,
        fallback_on_error,
        resolved_mode,
        translated_texts,
        local_cache,
        glossary,
        use_tm,
        tone,
        vision_context,
        on_progress,
        llm_context=llm_context,
    )

    if tasks:
        # Wrap tasks with a semaphore if it's Ollama to prevent overloading
        final_tasks = tasks
        if resolved_provider == "ollama":
            sem = asyncio.Semaphore(2)

            async def sem_wrapped_task(task):
                async with sem:
                    return await task

            final_tasks = [sem_wrapped_task(t) for t in tasks]

        if hasattr(translator, "set_async_client"):
            async with httpx.AsyncClient(timeout=settings.ollama_timeout) as client:
                translator.set_async_client(client)
                await asyncio.gather(*final_tasks)
        else:
            await asyncio.gather(*final_tasks)

    final_texts = [text if text is not None else "" for text in translated_texts]

    # Result Migration Pass (Bilingual Alignment)
    for i, block in enumerate(blocks_list):
        if block.get("alignment_role") == "source":
            # For Source blocks in a pair, we show original text to prevent redundant output items
            final_texts[i] = block.get("source_text", "")

    return build_contract(
        blocks=blocks_list,
        translated_texts=final_texts,
        target_language=target_language,
    )
