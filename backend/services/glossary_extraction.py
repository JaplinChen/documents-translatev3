from __future__ import annotations

import json
import logging
import os

from backend.services.llm_clients import (
    GeminiTranslator,
    MockTranslator,
    OllamaTranslator,
    OpenAITranslator,
    TranslationConfig,
)
from backend.services.translate_config import (
    get_language_hint,
    get_language_label,
)

LOGGER = logging.getLogger(__name__)


def _parse_json_array(content: str) -> list:
    """
    Parse JSON array from LLM response.
    Handles both raw JSON and markdown-wrapped JSON.
    """
    if not content or not content.strip():
        return []

    text = content.strip()

    # Try direct parse first
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
        return []
    except json.JSONDecodeError:
        pass

    # Try to find JSON array pattern [...]
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            result = json.loads(text[start:end + 1])
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    return []


def extract_glossary_terms(  # noqa: C901
    blocks: list[dict],
    target_language: str,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> list[dict[str, str]]:
    """
    Extract key terminology from PPTX blocks using LLM.
    Returns: [{"source": "...", "target": "...", "reason": "..."}]
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
                base_url=base_url
                or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
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
                base_url=base_url
                or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            )
        else:
            client = MockTranslator()

    # Consolidate all text for extraction
    # Support both 'original_text' (frontend) and 'source_text' (legacy).
    full_text = "\n".join(
        [
            b.get("original_text") or b.get("source_text", "")
            for b in blocks
            if b.get("original_text") or b.get("source_text")
        ]
    )
    if not full_text.strip():
        LOGGER.warning(
            "No text content found in blocks for glossary extraction"
        )
        return []

    # Limit text size to avoid token limit
    text_sample = full_text[:10000]

    from backend.services.prompt_store import render_prompt
    prompt = render_prompt(
        "glossary_extraction",
        {
            "target_language": get_language_label(target_language),
            "text_sample": text_sample,
            "language_hint": get_language_hint(target_language),
        },
    )

    try:
        if hasattr(client, "complete"):
            response = client.complete(prompt)
        elif hasattr(client, "translate_plain"):
            response = client.translate_plain(prompt)
        else:
            return []

        # Parse JSON array from response
        # _parse_json_array handles markdown code blocks and raw JSON
        return _parse_json_array(response)
    except ConnectionError as e:
        # Connection errors should be raised to inform the user
        LOGGER.error(f"Connection error extracting glossary: {e}")
        raise RuntimeError(str(e)) from e
    except Exception as e:
        error_msg = str(e)
        LOGGER.error(f"Error extracting glossary: {error_msg}")
        # If it's a connection-related error, raise it
        if (
            "連線" in error_msg
            or "connect" in error_msg.lower()
            or "connection" in error_msg.lower()
        ):
            raise RuntimeError(error_msg) from e
        # For other errors (like JSON parsing), return empty list
        return []
