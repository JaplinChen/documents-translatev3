from __future__ import annotations

from typing import Any

from backend.services.llm_context import build_context
from backend.services.translate_chunk import prepare_chunk, translate_chunk
from backend.services.translate_retry import apply_translation_results


def _translate_chunk_sync(
    translator,
    resolved_provider: str,
    chunk: list,
    target_language: str,
    blocks_list: list[dict],
    params: dict[str, Any],
    preferred_terms: list[tuple[str, str]],
    tone: str | None,
    vision_context: bool,
    fallback_on_error: bool,
    resolved_mode: str,
    use_placeholders: bool,
    llm_context: dict[str, Any],
    translated_texts: list[str | None],
    local_cache: dict,
    glossary: dict | None,
    use_tm: bool,
    chunk_index: int,
) -> None:
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
        chunk_index=chunk_index,
        fallback_on_error=fallback_on_error,
        mode=resolved_mode,
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


def _finalize_texts(
    blocks_list: list[dict],
    translated_texts: list[str | None],
) -> list[str]:
    final_texts = [text if text is not None else "" for text in translated_texts]
    for i, block in enumerate(blocks_list):
        if block.get("alignment_role") == "source":
            final_texts[i] = block.get("source_text", "")
    return final_texts
