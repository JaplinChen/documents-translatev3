"""Protocol definitions for translator interfaces.

This module defines the Protocol classes for type-safe translator usage.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, runtime_checkable

@runtime_checkable
class TranslatorProtocol(Protocol):
    """Protocol for all translator implementations."""

    def translate(
        self,
        blocks: Iterable[dict],
        target_language: str,
        context: dict | None = None,
        preferred_terms: list[tuple[str, str]] | None = None,
        placeholder_tokens: list[str] | None = None,
        language_hint: str | None = None,
    ) -> dict:
        """Translate blocks synchronously."""
        ...

    async def translate_async(
        self,
        blocks: Iterable[dict],
        target_language: str,
        context: dict | None = None,
        preferred_terms: list[tuple[str, str]] | None = None,
        placeholder_tokens: list[str] | None = None,
        language_hint: str | None = None,
    ) -> dict:
        """Translate blocks asynchronously."""
        ...

    def translate_plain(self, prompt: str) -> str:
        """Translate using plain text prompt."""
        ...

    async def translate_plain_async(self, prompt: str) -> str:
        """Translate using plain text prompt asynchronously."""
        ...
