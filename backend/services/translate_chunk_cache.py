"""Translation chunk caching utilities.

This module contains cache-related functions for translation chunks.
"""

from __future__ import annotations
from typing import Callable

from backend.services.translation_cache import cache


def get_from_cache(
    chunk_blocks: list[dict], target_language: str, provider: str, model: str, **kwargs
) -> tuple[list[dict | None], list[int]]:
    """Get blocks from cache and return final list and uncached indices."""
    final_blocks = []
    uncached_indices = []
    for i, block in enumerate(chunk_blocks):
        cached = cache.get(
            block.get("source_text", ""),
            target_language,
            provider,
            model,
            tone=kwargs.get("tone"),
            vision_context=kwargs.get("vision_context", True)
        )
        if cached:
            final_blocks.append({**block, "translated_text": cached})
        else:
            final_blocks.append(None)
            uncached_indices.append(i)
    return final_blocks, uncached_indices


def translate_and_cache_blocks(
    translator,
    provider: str,
    chunk_blocks: list[dict],
    uncached_indices: list[int],
    final_blocks: list[dict | None],
    target_language: str,
    context: dict | None,
    preferred_terms: list,
    placeholder_tokens: list,
    tone: str | None,
    vision_context: bool,
    params: dict,
    dispatch_func: Callable,
    mode: str = "direct",
) -> dict:
    """Translate uncached blocks and update cache."""
    blocks_to_translate = [chunk_blocks[i] for i in uncached_indices]

    result = dispatch_func(
        translator,
        provider,
        blocks_to_translate,
        target_language,
        context,
        preferred_terms,
        placeholder_tokens,
        tone,
        vision_context,
        mode=mode,
    )

    res_blocks = result.get("blocks", [])
    for i, res_block in enumerate(res_blocks):
        original_idx = uncached_indices[i]
        translated_text = res_block.get("translated_text", "")
        final_blocks[original_idx] = res_block
        cache.set(
            chunk_blocks[original_idx].get("source_text", ""),
            target_language,
            provider,
            params.get("model", "default"),
            translated_text,
            tone=tone,
            vision_context=vision_context
        )

    result["blocks"] = final_blocks
    return result


async def translate_and_cache_blocks_async(
    translator,
    provider: str,
    chunk_blocks: list[dict],
    uncached_indices: list[int],
    final_blocks: list[dict | None],
    target_language: str,
    context: dict | None,
    preferred_terms: list,
    placeholder_tokens: list,
    tone: str | None,
    vision_context: bool,
    params: dict,
    dispatch_func: Callable,
    mode: str = "direct",
) -> dict:
    """Translate uncached blocks and update cache (Async)."""
    blocks_to_translate = [chunk_blocks[i] for i in uncached_indices]

    result = await dispatch_func(
        translator,
        provider,
        blocks_to_translate,
        target_language,
        context,
        preferred_terms,
        placeholder_tokens,
        tone,
        vision_context,
        mode=mode,
    )

    res_blocks = result.get("blocks", [])
    for i, res_block in enumerate(res_blocks):
        original_idx = uncached_indices[i]
        translated_text = res_block.get("translated_text", "")
        final_blocks[original_idx] = res_block
        cache.set(
            chunk_blocks[original_idx].get("source_text", ""),
            target_language,
            provider,
            params.get("model", "default"),
            translated_text,
            tone=tone,
            vision_context=vision_context
        )

    result["blocks"] = final_blocks
    return result
