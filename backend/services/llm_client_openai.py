"""OpenAI API client for translation.

This module provides the OpenAITranslator class for interacting
with OpenAI's chat completions API.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable

import httpx

from backend.config import settings
from backend.services.llm_client_base import TranslationConfig, load_contract_example
from backend.services.llm_contract import validate_contract
from backend.services.llm_prompt import build_prompt
from backend.services.prompt_store import get_prompt
from backend.services.token_tracker import record_usage

LOGGER = logging.getLogger(__name__)


class OpenAITranslator:
    """Translator using OpenAI's chat completions API."""

    def __init__(self, config: TranslationConfig) -> None:
        self.config = config

    def translate(
        self,
        blocks: Iterable[dict],
        target_language: str,
        context: dict | None = None,
        preferred_terms: list[tuple[str, str]] | None = None,
        placeholder_tokens: list[str] | None = None,
        language_hint: str | None = None,
        mode: str = "direct",
    ) -> dict:
        """Translate blocks using OpenAI API (Synchronous)."""
        contract_example = load_contract_example()
        prompt = build_prompt(
            blocks,
            target_language,
            contract_example,
            context,
            preferred_terms,
            placeholder_tokens,
            language_hint,
            mode=mode,
        )

        system_message = self._get_system_message()
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.config.base_url}/chat/completions"

        with httpx.Client(timeout=settings.openai_timeout) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            response_data = response.json()

        # Record usage
        if "usage" in response_data:
            usage = response_data["usage"]
            record_usage(
                provider="openai",
                model=self.config.model,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
            )

        content = response_data["choices"][0]["message"]["content"]
        result = json.loads(content)
        validate_contract(result)
        return result

    async def translate_async(
        self,
        blocks: Iterable[dict],
        target_language: str,
        context: dict | None = None,
        preferred_terms: list[tuple[str, str]] | None = None,
        placeholder_tokens: list[str] | None = None,
        language_hint: str | None = None,
        mode: str = "direct",
    ) -> dict:
        """Translate blocks using OpenAI API (Asynchronous)."""
        contract_example = load_contract_example()
        prompt = build_prompt(
            blocks,
            target_language,
            contract_example,
            context,
            preferred_terms,
            placeholder_tokens,
            language_hint,
            mode=mode,
        )

        system_message = self._get_system_message()
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.config.base_url}/chat/completions"

        async with httpx.AsyncClient(timeout=settings.openai_timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            response_data = response.json()

        # Record usage
        if "usage" in response_data:
            usage = response_data["usage"]
            record_usage(
                provider="openai",
                model=self.config.model,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
            )

        content = response_data["choices"][0]["message"]["content"]
        result = json.loads(content)
        validate_contract(result)
        return result

    def _get_system_message(self) -> str:
        try:
            return get_prompt("system_message")
        except FileNotFoundError:
            return "你是負責翻譯 PPTX 文字區塊的助手。只回傳 JSON，且必須符合既定 schema。"

    def complete(self, prompt: str, system_message: str | None = None) -> str:
        """Complete a prompt using OpenAI API (Synchronous)."""
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_message or "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
        }
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.config.base_url}/chat/completions"
        with httpx.Client(timeout=settings.openai_timeout) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            response_data = response.json()
        return response_data["choices"][0]["message"]["content"]

    async def complete_async(self, prompt: str, system_message: str | None = None) -> str:
        """Complete a prompt using OpenAI API (Asynchronous)."""
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_message or "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
        }
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.config.base_url}/chat/completions"
        async with httpx.AsyncClient(timeout=settings.openai_timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            response_data = response.json()
        return response_data["choices"][0]["message"]["content"]
