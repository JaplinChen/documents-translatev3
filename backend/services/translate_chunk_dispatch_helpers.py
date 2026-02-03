from __future__ import annotations

from backend.services.translate_config import (
    get_language_hint,
    get_tone_instruction,
    get_vision_context_instruction,
)


def build_custom_hint(
    target_language: str,
    tone: str | None,
    vision_context: bool,
) -> str:
    hint = get_language_hint(target_language)
    tone_hint = get_tone_instruction(tone)
    vision_hint = get_vision_context_instruction(vision_context)
    return f"{hint}\n{tone_hint}\n{vision_hint}".strip()


def safe_translate(
    translator,
    chunk_blocks,
    target_language,
    context,
    preferred_terms,
    placeholder_tokens,
    custom_hint,
    mode: str,
):
    try:
        return translator.translate(
            chunk_blocks,
            target_language,
            context=context,
            preferred_terms=preferred_terms,
            placeholder_tokens=placeholder_tokens,
            language_hint=custom_hint,
            mode=mode,
        )
    except TypeError:
        return translator.translate(
            chunk_blocks,
            target_language,
            context=context,
            preferred_terms=preferred_terms,
            placeholder_tokens=placeholder_tokens,
            language_hint=custom_hint,
        )


async def safe_translate_async(
    translator,
    chunk_blocks,
    target_language,
    context,
    preferred_terms,
    placeholder_tokens,
    custom_hint,
    mode: str,
):
    try:
        return await translator.translate_async(
            chunk_blocks,
            target_language,
            context=context,
            preferred_terms=preferred_terms,
            placeholder_tokens=placeholder_tokens,
            language_hint=custom_hint,
            mode=mode,
        )
    except TypeError:
        return await translator.translate_async(
            chunk_blocks,
            target_language,
            context=context,
            preferred_terms=preferred_terms,
            placeholder_tokens=placeholder_tokens,
            language_hint=custom_hint,
        )
