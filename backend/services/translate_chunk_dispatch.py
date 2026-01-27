"""Translation dispatch and provider-specific utilities.

This module contains functions for dispatching translations to different
providers and handling provider-specific logic.
"""

from __future__ import annotations

from backend.services.llm_clients import MockTranslator
from backend.services.llm_contract import build_contract, coerce_contract, validate_contract
from backend.services.translate_config import (
    get_language_hint,
    get_tone_instruction,
    get_vision_context_instruction,
)
from backend.services.translate_prompt import (
    build_ollama_batch_prompt,
    parse_ollama_batch_response,
)
from backend.services.translate_retry import (
    build_language_retry_context,
    has_language_mismatch,
)


def dispatch_translate(
    translator,
    provider,
    blocks_to_translate,
    target_language,
    context,
    preferred_terms,
    placeholder_tokens,
    tone,
    vision_context,
    mode: str = "direct",
):
    """Dispatch to correct translator sync."""
    if provider == "ollama":
        return translate_ollama(
            translator,
            blocks_to_translate,
            target_language,
            context,
            preferred_terms,
            placeholder_tokens,
            tone,
            vision_context,
            mode=mode,
        )
    return translate_standard(
        translator,
        blocks_to_translate,
        target_language,
        context,
        preferred_terms,
        placeholder_tokens,
        tone,
        vision_context,
        mode=mode,
    )


async def dispatch_translate_async(
    translator,
    provider,
    blocks_to_translate,
    target_language,
    context,
    preferred_terms,
    placeholder_tokens,
    tone,
    vision_context,
    mode: str = "direct",
):
    """Dispatch to correct translator async."""
    if provider == "ollama":
        return await translate_ollama_async(
            translator,
            blocks_to_translate,
            target_language,
            context,
            preferred_terms,
            placeholder_tokens,
            tone,
            vision_context,
            mode=mode,
        )
    return await translate_standard_async(
        translator,
        blocks_to_translate,
        target_language,
        context,
        preferred_terms,
        placeholder_tokens,
        tone,
        vision_context,
        mode=mode,
    )


def translate_ollama(
    translator,
    chunk_blocks,
    target_language,
    context,
    preferred_terms,
    placeholder_tokens,
    tone,
    vision_context,
    mode: str = "direct",
):
    """Handle Ollama-specific translation."""
    prompt = build_ollama_batch_prompt(chunk_blocks, target_language)
    text_output = translator.translate_plain(prompt)
    translated_texts_chunk = parse_ollama_batch_response(text_output, len(chunk_blocks))

    if translated_texts_chunk is None:
        custom_hint = build_custom_hint(target_language, tone, vision_context)
        result = translator.translate(
            chunk_blocks,
            target_language,
            context=context,
            preferred_terms=preferred_terms,
            placeholder_tokens=placeholder_tokens,
            language_hint=custom_hint,
            mode=mode,
        )
        result = coerce_contract(result, chunk_blocks, target_language)
    else:
        result = build_contract(chunk_blocks, target_language, translated_texts_chunk)

    validate_contract(result)
    return result


async def translate_ollama_async(
    translator,
    chunk_blocks,
    target_language,
    context,
    preferred_terms,
    placeholder_tokens,
    tone,
    vision_context,
    mode: str = "direct",
):
    """Handle Ollama-specific translation (Async)."""
    prompt = build_ollama_batch_prompt(chunk_blocks, target_language)
    text_output = await translator.translate_plain_async(prompt)
    translated_texts_chunk = parse_ollama_batch_response(text_output, len(chunk_blocks))

    if translated_texts_chunk is None:
        custom_hint = build_custom_hint(target_language, tone, vision_context)
        result = await translator.translate_async(
            chunk_blocks,
            target_language,
            context=context,
            preferred_terms=preferred_terms,
            placeholder_tokens=placeholder_tokens,
            language_hint=custom_hint,
            mode=mode,
        )
        result = coerce_contract(result, chunk_blocks, target_language)
    else:
        result = build_contract(chunk_blocks, target_language, translated_texts_chunk)

    validate_contract(result)
    return result


def translate_standard(
    translator,
    chunk_blocks,
    target_language,
    context,
    preferred_terms,
    placeholder_tokens,
    tone,
    vision_context,
    mode: str = "direct",
):
    """Handle standard translation."""
    custom_hint = build_custom_hint(target_language, tone, vision_context)
    result = translator.translate(
        chunk_blocks,
        target_language,
        context=context,
        preferred_terms=preferred_terms,
        placeholder_tokens=placeholder_tokens,
        language_hint=custom_hint,
        mode=mode,
    )
    result = coerce_contract(result, chunk_blocks, target_language)
    validate_contract(result)
    return result


async def translate_standard_async(
    translator,
    chunk_blocks,
    target_language,
    context,
    preferred_terms,
    placeholder_tokens,
    tone,
    vision_context,
    mode: str = "direct",
):
    """Handle standard translation (Async)."""
    custom_hint = build_custom_hint(target_language, tone, vision_context)
    result = await translator.translate_async(
        chunk_blocks,
        target_language,
        context=context,
        preferred_terms=preferred_terms,
        placeholder_tokens=placeholder_tokens,
        language_hint=custom_hint,
        mode=mode,
    )
    result = coerce_contract(result, chunk_blocks, target_language)
    validate_contract(result)
    return result


def build_custom_hint(target_language: str, tone: str | None, vision_context: bool) -> str:
    """Build custom hint string for translation."""
    hint = get_language_hint(target_language)
    tone_hint = get_tone_instruction(tone)
    vision_hint = get_vision_context_instruction(vision_context)
    return f"{hint}\n{tone_hint}\n{vision_hint}".strip()


    return result
