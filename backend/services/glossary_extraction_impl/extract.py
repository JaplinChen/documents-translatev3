from __future__ import annotations

import logging
import os

from backend.services.llm_clients import (
    GeminiTranslator,
    MockTranslator,
    OllamaTranslator,
    OpenAITranslator,
    TranslationConfig,
)
from backend.services.translate_config import get_language_hint, get_language_label
from backend.services.learning_service import detect_domain, get_learned_terms
from backend.services.prompt_store import render_prompt

from .constants import IT_BRAND_HINTS
from .utils import _load_existing_terms, _parse_json_array, _suggest_typo_corrections
from .validation import _validate_and_filter_terms

LOGGER = logging.getLogger(__name__)


def extract_glossary_terms(  # noqa: C901
    blocks: list[dict],
    target_language: str,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> dict:
    """
    Extract key terminology from document blocks using LLM.
    Returns: {"terms": [...], "domain": "..."}
    """
    mode = os.getenv("TRANSLATE_LLM_MODE", "real").lower()

    if mode == "mock":
        client = MockTranslator()
    else:
        resolved_provider = (provider or "openai").lower()
        if resolved_provider in {"openai", "chatgpt", "gpt-4o"}:
            config = TranslationConfig(
                model=model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                api_key=api_key or os.getenv("OPENAI_API_KEY", ""),
                base_url=base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            )
            client = OpenAITranslator(config)
        elif resolved_provider == "gemini":
            client = GeminiTranslator(
                api_key=api_key or os.getenv("GEMINI_API_KEY", ""),
                base_url=base_url
                or os.getenv(
                    "GEMINI_BASE_URL",
                    "https://generativelanguage.googleapis.com/v1beta",
                ),
                model=model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            )
        elif resolved_provider == "ollama":
            client = OllamaTranslator(
                model=model or os.getenv("OLLAMA_MODEL", "llama3.1"),
                base_url=base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            )
        else:
            client = MockTranslator()

    full_text = "\n".join(
        [
            block.get("original_text") or block.get("source_text", "")
            for block in blocks
            if block.get("original_text") or block.get("source_text")
        ]
    )
    if not full_text.strip():
        LOGGER.warning("No text content found in blocks for glossary extraction")
        return []

    text_sample = full_text[:10000]

    existing_terms = _load_existing_terms(target_language)
    existing_terms_set = set(term.lower() for term in existing_terms)

    if existing_terms:
        existing_display = existing_terms[:100]
        existing_terms_str = ", ".join(existing_display)
        if len(existing_terms) > 100:
            existing_terms_str += f" ... (還有 {len(existing_terms) - 100} 個)"
    else:
        existing_terms_str = "(無)"

    typo_hints = _suggest_typo_corrections(text_sample)
    brand_context = ", ".join(IT_BRAND_HINTS)

    domain = detect_domain(text_sample)
    learned = get_learned_terms(target_language, min_count=2, limit=20)
    if learned:
        learned_str = "\n".join([f"- {item['source']} -> {item['target']}" for item in learned])
    else:
        learned_str = "(尚無使用者習慣紀錄)"

    prompt = render_prompt(
        "glossary_extraction",
        {
            "target_language": get_language_label(target_language),
            "text_sample": text_sample,
            "language_hint": get_language_hint(target_language),
            "existing_terms": existing_terms_str,
            "typo_hints": typo_hints or "(無)",
            "brand_hints": brand_context,
            "domain_context": domain,
            "learned_context": learned_str,
        },
    )

    try:
        if hasattr(client, "complete"):
            response = client.complete(prompt)
        elif hasattr(client, "translate_plain"):
            response = client.translate_plain(prompt)
        else:
            return []

        raw_terms = _parse_json_array(response)
        terms = _validate_and_filter_terms(raw_terms, existing_terms_set)
        return {"terms": terms, "domain": domain}

    except ConnectionError as exc:
        LOGGER.error(f"Connection error extracting glossary: {exc}")
        raise RuntimeError(str(exc)) from exc
    except Exception as exc:
        error_msg = str(exc)
        LOGGER.error(f"Error extracting glossary: {error_msg}")
        if (
            "連線" in error_msg
            or "connect" in error_msg.lower()
            or "connection" in error_msg.lower()
        ):
            raise RuntimeError(error_msg) from exc
        return []
