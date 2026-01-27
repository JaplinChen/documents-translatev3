"""Base classes and shared utilities for LLM clients.

This module contains the TranslationConfig dataclass, contract loading,
and the MockTranslator implementation.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from backend.services.llm_contract import build_contract

CONTRACT_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "translation_contract_pptx.json"
)


def load_contract_example() -> dict:
    """Load the translation contract example from docs."""
    if not CONTRACT_PATH.exists():
        raise FileNotFoundError(f"Missing contract file: {CONTRACT_PATH}")
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class TranslationConfig:
    """Configuration for translation clients."""

    model: str
    api_key: str
    base_url: str


class MockTranslator:
    """Mock translator for testing and fallback."""

    def translate(
        self,
        blocks: Iterable[dict],
        target_language: str,
        context: dict | None = None,
        preferred_terms: list[tuple[str, str]] | None = None,
        placeholder_tokens: list[str] | None = None,
        language_hint: str | None = None,
    ) -> dict:
        """Return original text as translation (mock mode)."""
        return build_contract(blocks, target_language, translated_texts=None)

    async def translate_async(
        self,
        blocks: Iterable[dict],
        target_language: str,
        context: dict | None = None,
        preferred_terms: list[tuple[str, str]] | None = None,
        placeholder_tokens: list[str] | None = None,
        language_hint: str | None = None,
    ) -> dict:
        """Return original text as translation (mock mode)."""
        return self.translate(
            blocks,
            target_language,
            context,
            preferred_terms,
            placeholder_tokens,
            language_hint,
        )

    def complete(self, prompt: str) -> str:
        """Return mock response for completions."""
        return "MOCK_RESPONSE"

    async def complete_async(self, prompt: str) -> str:
        """Return mock response for completions."""
        return self.complete(prompt)

    def translate_plain(self, prompt: str) -> str:
        """Return mock response for plain text translation."""
        return prompt

    async def translate_plain_async(self, prompt: str) -> str:
        """Return mock response for plain text translation."""
        return self.translate_plain(prompt)
