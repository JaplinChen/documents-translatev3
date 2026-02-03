"""Translation chunk processing utilities.

This module contains chunk-level translation logic including
preparation, execution, and retry handling.
"""

from __future__ import annotations

import asyncio
import logging
import time
from backend.services.llm_placeholders import apply_placeholders
from backend.services.translate_chunk_cache import (
    get_from_cache,
    translate_and_cache_blocks,
    translate_and_cache_blocks_async,
)
from backend.services.translate_chunk_dispatch import (
    dispatch_translate,
    dispatch_translate_async,
)
from backend.services.translate_retry import (
    fallback_mock,
    fallback_mock_async,
    has_language_mismatch,
    retry_for_language,
    retry_for_language_async,
)
from backend.services.translate_chunk_utils import (
    calculate_backoff,
    detect_top_language,
    is_vision_error,
)

LOGGER = logging.getLogger(__name__)


def prepare_chunk(
    chunk: list[tuple[int, dict]],
    use_placeholders: bool,
    preferred_terms: list[tuple[str, str]],
) -> tuple[list[dict], list[dict], list[str]]:
    """Prepare a chunk of blocks for translation."""
    chunk_blocks = []
    placeholder_maps: list[dict[str, str]] = []
    placeholder_tokens: list[str] = []

    for _, block in chunk:
        prepared = dict(block)
        if use_placeholders:
            prepared_text, mapping = apply_placeholders(
                prepared.get("source_text", ""), preferred_terms
            )
        else:
            prepared_text = prepared.get("source_text", "")
            mapping = {}
        prepared["source_text"] = prepared_text
        if mapping:
            placeholder_tokens.extend(mapping.keys())
        placeholder_maps.append(mapping)
        chunk_blocks.append(prepared)

    return chunk_blocks, placeholder_maps, placeholder_tokens


def translate_chunk(
    translator,
    provider: str,
    chunk_blocks: list[dict],
    target_language: str,
    context: dict | None,
    preferred_terms: list,
    placeholder_tokens: list,
    tone: str | None,
    vision_context: bool,
    params: dict,
    chunk_index: int,
    fallback_on_error: bool,
    mode: str,
) -> dict:
    """Translate a single chunk with retry logic."""
    attempt = 0
    retried_for_language = False

    while True:
        try:
            attempt += 1
            LOGGER.info(
                "LLM chunk %s attempt %s size=%s",
                chunk_index,
                attempt,
                len(chunk_blocks),
            )

            refresh = params.get("refresh", False)
            if refresh:
                final_blocks = [None] * len(chunk_blocks)
                uncached_indices = list(range(len(chunk_blocks)))
            else:
                final_blocks, uncached_indices = get_from_cache(
                    chunk_blocks,
                    target_language,
                    provider,
                    params.get("model", "default"),
                    tone=tone,
                    vision_context=vision_context,
                )

            if not uncached_indices:
                return {"blocks": final_blocks}

            result = translate_and_cache_blocks(
                translator,
                provider,
                chunk_blocks,
                uncached_indices,
                final_blocks,
                target_language,
                context,
                preferred_terms,
                placeholder_tokens,
                tone,
                vision_context,
                params,
                dispatch_translate,
                mode=mode,
            )

            chunk_texts = [
                item.get("translated_text", "")
                for item in result["blocks"]
            ]
            if not retried_for_language and has_language_mismatch(
                chunk_texts,
                target_language,
            ):
                retried_for_language = True
                result = retry_for_language(
                    translator,
                    provider,
                    chunk_blocks,
                    target_language,
                    context,
                    preferred_terms,
                    placeholder_tokens,
                    chunk_texts,
                )

            return result

        except Exception as exc:
            if is_vision_error(str(exc)):
                raise ValueError("偵測到圖片相關錯誤") from exc

            if attempt > params["max_retries"]:
                if fallback_on_error and mode != "mock":
                    return fallback_mock(
                        chunk_blocks,
                        target_language,
                        context,
                        preferred_terms,
                        placeholder_tokens,
                    )
                raise

            sleep_for = calculate_backoff(
                exc,
                attempt,
                params["backoff"],
                params["max_backoff"],
            )
            time.sleep(sleep_for)


async def translate_chunk_async(
    translator,
    provider: str,
    chunk_blocks: list[dict],
    target_language: str,
    context: dict | None,
    preferred_terms: list,
    placeholder_tokens: list,
    tone: str | None,
    vision_context: bool,
    params: dict,
    chunk_index: int,
    fallback_on_error: bool,
    mode: str,
) -> dict:
    """Translate a single chunk with retry logic (Async)."""
    attempt = 0
    retried_for_language = False

    while True:
        try:
            attempt += 1
            LOGGER.info(
                "LLM chunk %s attempt %s size=%s (async)",
                chunk_index,
                attempt,
                len(chunk_blocks),
            )

            refresh = params.get("refresh", False)
            if refresh:
                final_blocks = [None] * len(chunk_blocks)
                uncached_indices = list(range(len(chunk_blocks)))
            else:
                final_blocks, uncached_indices = get_from_cache(
                    chunk_blocks,
                    target_language,
                    provider,
                    params.get("model", "default"),
                    tone=tone,
                    vision_context=vision_context,
                )

            if not uncached_indices:
                return {"blocks": final_blocks}

            result = await translate_and_cache_blocks_async(
                translator,
                provider,
                chunk_blocks,
                uncached_indices,
                final_blocks,
                target_language,
                context,
                preferred_terms,
                placeholder_tokens,
                tone,
                vision_context,
                params,
                dispatch_translate_async,
                mode=mode,
            )

            chunk_texts = [
                item.get("translated_text", "")
                for item in result["blocks"]
            ]
            if not retried_for_language and has_language_mismatch(
                chunk_texts,
                target_language,
            ):
                retried_for_language = True
                result = await retry_for_language_async(
                    translator,
                    provider,
                    chunk_blocks,
                    target_language,
                    context,
                    preferred_terms,
                    placeholder_tokens,
                    chunk_texts,
                )

            return result

        except Exception as exc:
            if is_vision_error(str(exc)):
                raise ValueError("偵測到圖片相關錯誤") from exc

            if attempt > params["max_retries"]:
                if fallback_on_error and mode != "mock":
                    return await fallback_mock_async(
                        chunk_blocks,
                        target_language,
                        context,
                        preferred_terms,
                        placeholder_tokens,
                    )
                raise

            sleep_for = calculate_backoff(
                exc,
                attempt,
                params["backoff"],
                params["max_backoff"],
            )
            await asyncio.sleep(sleep_for)
