"""Translation chunk processing utilities.

This module contains chunk-level translation logic including
preparation, execution, and retry handling.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from urllib.error import HTTPError

from backend.services.language_detect import detect_language
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
    has_language_mismatch,
    fallback_mock,
    fallback_mock_async,
    retry_for_language,
    retry_for_language_async,
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
                    vision_context=vision_context
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

            chunk_texts = [item.get("translated_text", "") for item in result["blocks"]]
            if not retried_for_language and has_language_mismatch(chunk_texts, target_language):
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
            if _is_vision_error(str(exc)):
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

            sleep_for = _calculate_backoff(exc, attempt, params["backoff"], params["max_backoff"])
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
                    vision_context=vision_context
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

            chunk_texts = [item.get("translated_text", "") for item in result["blocks"]]
            if not retried_for_language and has_language_mismatch(chunk_texts, target_language):
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
            if _is_vision_error(str(exc)):
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

            sleep_for = _calculate_backoff(exc, attempt, params["backoff"], params["backoff"])
            await asyncio.sleep(sleep_for)


def detect_top_language(texts: list[str]) -> str | None:
    """Detect the most common language in texts."""
    counts: dict[str, int] = {}
    for text in texts:
        detected = detect_language((text or "").strip())
        if detected:
            counts[detected] = counts.get(detected, 0) + 1
    if not counts:
        return None
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)[0][0]


def _is_vision_error(error_msg: str) -> bool:
    """Check if error is related to vision/image."""
    lower = error_msg.lower()
    return "image" in lower or "vision" in lower


def _calculate_backoff(exc: Exception, attempt: int, backoff: float, max_backoff: float) -> float:
    """Calculate backoff time for retry."""
    retry_after = None
    if isinstance(exc, HTTPError) and exc.code in {429, 503}:
        retry_after = exc.headers.get("Retry-After")
    if retry_after:
        try:
            return max(float(retry_after), 0)
        except ValueError:
            pass
    return min(backoff * attempt, max_backoff) + random.uniform(0, 0.5)
