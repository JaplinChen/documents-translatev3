from __future__ import annotations

from typing import Any

from backend.config import settings
from backend.services.bilingual_alignment import align_bilingual_blocks
from backend.services.learning_service import detect_domain
from backend.services.llm_contract import build_contract
from backend.services.llm_glossary import load_glossary
from backend.services.translate_llm_helpers import load_preferred_terms, prepare_pending_blocks

from .helpers import _determine_chunk_size, _prepare_params, _resolve_translator


def prepare_translation_context(
    blocks: list[dict],
    target_language: str,
    source_language: str | None,
    provider: str | None,
    model: str | None,
    api_key: str | None,
    base_url: str | None,
    use_tm: bool,
    tone: str | None,
    vision_context: bool,
    scope_type: str | None,
    scope_id: str | None,
    domain: str | None,
    category: str | None,
    param_overrides: dict | None,
    mode: str | None,
) -> dict[str, Any]:
    resolved_mode = (mode or settings.translate_llm_mode).lower()
    fallback_on_error = settings.llm_fallback_on_error
    resolved_provider, translator = _resolve_translator(
        resolved_mode, provider, model, api_key, base_url, fallback_on_error
    )

    blocks_list = list(blocks)
    source_lang = source_language or settings.source_language
    if resolved_mode != "mock":
        blocks_list = align_bilingual_blocks(
            blocks_list,
            source_lang,
            target_language,
        )

    if not domain:
        sample_text = " ".join(
            b.get("source_text", "").strip() for b in blocks_list[:20] if b.get("source_text")
        )
        domain = detect_domain(sample_text)

    preferred_terms = load_preferred_terms(
        source_lang,
        target_language,
        use_tm,
    )
    use_placeholders = resolved_provider != "ollama"

    param_overrides = (param_overrides or {}).copy()
    refresh = param_overrides.get("refresh", False)

    llm_context = {
        "provider": resolved_provider,
        "model": model,
        "tone": tone,
        "vision_context": vision_context,
        "scope_type": scope_type,
        "scope_id": scope_id,
        "domain": domain,
        "category": category,
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

    params = _prepare_params(
        resolved_provider,
        param_overrides,
        model,
        tone,
        vision_context,
    )
    chunk_size = _determine_chunk_size(pending, params)

    glossary = load_glossary(params["glossary_path"])

    return {
        "resolved_mode": resolved_mode,
        "fallback_on_error": fallback_on_error,
        "resolved_provider": resolved_provider,
        "translator": translator,
        "blocks_list": blocks_list,
        "source_lang": source_lang,
        "domain": domain,
        "preferred_terms": preferred_terms,
        "use_placeholders": use_placeholders,
        "param_overrides": param_overrides,
        "llm_context": llm_context,
        "translated_texts": translated_texts,
        "pending": pending,
        "local_cache": local_cache,
        "params": params,
        "chunk_size": chunk_size,
        "glossary": glossary,
    }
