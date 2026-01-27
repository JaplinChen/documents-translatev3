"""LLM client facade module.

This module re-exports all LLM client classes for backward compatibility.
Import from this module to access any translator implementation.
"""

from __future__ import annotations

from backend.services.llm_client_base import (
    MockTranslator,
    TranslationConfig,
    load_contract_example,
)
from backend.services.llm_client_gemini import GeminiTranslator
from backend.services.llm_client_ollama import (
    OllamaTranslator,
    build_ollama_options,
)
from backend.services.llm_client_openai import OpenAITranslator

__all__ = [
    "TranslationConfig",
    "MockTranslator",
    "OpenAITranslator",
    "GeminiTranslator",
    "OllamaTranslator",
    "build_ollama_options",
    "load_contract_example",
]
