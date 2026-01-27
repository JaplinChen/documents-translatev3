"""Translator selection and configuration utilities.

This module provides translator instantiation and parameter
configuration based on provider and environment settings.
"""

from __future__ import annotations

from backend.config import settings
from backend.services.llm_clients import (
    GeminiTranslator,
    MockTranslator,
    OllamaTranslator,
    OpenAITranslator,
    TranslationConfig,
)


def select_translator(
    provider: str | None,
    model: str | None,
    api_key: str | None,
    base_url: str | None,
    fallback_on_error: bool,
) -> tuple[str, object]:
    """Select and instantiate the appropriate translator.

    Args:
        provider: LLM provider name (openai, gemini, ollama)
        model: Model name to use
        api_key: API key for the provider
        base_url: Base URL for the API
        fallback_on_error: Whether to fallback to mock on error

    Returns:
        Tuple of (resolved_provider_name, translator_instance)
    """
    resolved_provider = (provider or "openai").lower()

    if resolved_provider in {"openai", "chatgpt", "gpt-4o"}:
        return _create_openai_translator(
            resolved_provider, model, api_key, base_url, fallback_on_error
        )

    if resolved_provider == "gemini":
        return _create_gemini_translator(model, api_key, base_url, fallback_on_error)

    if resolved_provider == "ollama":
        return _create_ollama_translator(model, base_url)

    return "mock", MockTranslator()


def _create_openai_translator(
    provider: str,
    model: str | None,
    api_key: str | None,
    base_url: str | None,
    fallback_on_error: bool,
) -> tuple[str, object]:
    """Create OpenAI translator instance."""
    resolved_key = api_key or settings.openai_api_key or ""
    if not resolved_key:
        if fallback_on_error:
            return "mock", MockTranslator()
        raise OSError("OPENAI_API_KEY is required for OpenAI translation")

    model_name = model or settings.openai_model
    if provider == "gpt-4o" and not model:
        model_name = "gpt-4o"

    config = TranslationConfig(
        model=model_name,
        api_key=resolved_key,
        base_url=base_url or settings.openai_base_url,
    )
    return "openai", OpenAITranslator(config)


def _create_gemini_translator(
    model: str | None,
    api_key: str | None,
    base_url: str | None,
    fallback_on_error: bool,
) -> tuple[str, object]:
    """Create Gemini translator instance."""
    resolved_key = api_key or settings.gemini_api_key or ""
    if not resolved_key:
        if fallback_on_error:
            return "mock", MockTranslator()
        raise OSError("GEMINI_API_KEY is required for Gemini translation")

    return "gemini", GeminiTranslator(
        api_key=resolved_key,
        base_url=base_url or settings.gemini_base_url,
        model=model or settings.gemini_model,
    )


def _create_ollama_translator(
    model: str | None,
    base_url: str | None,
) -> tuple[str, object]:
    """Create Ollama translator instance."""
    resolved_model = model or settings.ollama_model
    return "ollama", OllamaTranslator(
        model=resolved_model,
        base_url=base_url or settings.ollama_base_url,
    )


def get_translation_params(provider: str, overrides: dict | None = None) -> dict:
    """Get translation parameters based on provider and environment.

    Args:
        provider: LLM provider name
        overrides: Optional parameter overrides

    Returns:
        Dictionary with chunk_size, max_retries, chunk_delay, etc.
    """
    overrides = overrides or {}
    chunk_size = overrides.get("chunk_size", settings.llm_chunk_size)
    max_retries = overrides.get("max_retries", settings.llm_max_retries)
    chunk_delay = overrides.get("chunk_delay", settings.llm_chunk_delay)
    single_request = overrides.get("single_request", settings.llm_single_request)

    return {
        "chunk_size": chunk_size,
        "max_retries": max_retries,
        "chunk_delay": chunk_delay,
        "single_request": single_request,
        "backoff": settings.llm_retry_backoff,
        "max_backoff": settings.llm_retry_max_backoff,
        "context_strategy": settings.llm_context_strategy.lower(),
        "glossary_path": settings.llm_glossary_path or "",
        "model": overrides.get("model", settings.ollama_model),
        "tone": overrides.get("tone"),
        "vision_context": overrides.get("vision_context", True),
        "refresh": overrides.get("refresh", False),
    }
