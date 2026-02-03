from __future__ import annotations

from typing import Any

from backend.services.llm_clients import MockTranslator
from backend.services.translate_selector import get_translation_params, select_translator


def _resolve_translator(
    resolved_mode: str,
    provider: str | None,
    model: str | None,
    api_key: str | None,
    base_url: str | None,
    fallback_on_error: bool,
) -> tuple[str, Any]:
    if resolved_mode == "mock":
        return "mock", MockTranslator()
    return select_translator(
        provider,
        model,
        api_key,
        base_url,
        fallback_on_error,
    )


def _prepare_params(
    resolved_provider: str,
    overrides: dict[str, Any],
    model: str | None,
    tone: str | None,
    vision_context: bool,
) -> dict[str, Any]:
    overrides.update({"model": model, "tone": tone, "vision_context": vision_context})
    params = get_translation_params(resolved_provider, overrides=overrides)
    if params["single_request"]:
        params["chunk_delay"] = 0.0
    return params


def _determine_chunk_size(pending: list, params: dict[str, Any]) -> int:
    chunk_size = params["chunk_size"]
    if params["single_request"]:
        return len(pending) if pending else chunk_size
    return chunk_size
