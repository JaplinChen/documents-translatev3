"""Ollama local LLM client for translation.

This module provides the OllamaTranslator class and related utilities
for interacting with locally running Ollama instances.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable

import httpx

from backend.config import settings
from backend.services.llm_client_base import load_contract_example
from backend.services.llm_contract import validate_contract
from backend.services.llm_prompt import build_prompt
from backend.services.llm_utils import safe_json_loads
from backend.services.prompt_store import get_prompt
from backend.services.token_tracker import record_usage

LOGGER = logging.getLogger(__name__)


def build_ollama_options() -> dict:
    """Build Ollama-specific options from settings."""
    options: dict[str, int] = {}

    if settings.ollama_num_gpu is not None:
        options["num_gpu"] = settings.ollama_num_gpu
    if settings.ollama_num_gpu_layers is not None:
        options["num_gpu_layers"] = settings.ollama_num_gpu_layers
    if settings.ollama_num_ctx is not None:
        options["num_ctx"] = settings.ollama_num_ctx
    if settings.ollama_num_thread is not None:
        options["num_thread"] = settings.ollama_num_thread

    if settings.ollama_force_gpu and "num_gpu" not in options and "num_gpu_layers" not in options:
        options["num_gpu"] = 1

    return options


class OllamaTranslator:
    """Translator using locally running Ollama instance."""

    def __init__(self, model: str, base_url: str) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._async_client: httpx.AsyncClient | None = None

    def set_async_client(self, client: httpx.AsyncClient) -> None:
        """Set an external async client for connection pooling."""
        self._async_client = client

    def _post(self, endpoint: str, payload: dict) -> dict:
        """Make POST request to Ollama API (Synchronous)."""
        url = f"{self.base_url}{endpoint}"
        try:
            with httpx.Client(timeout=settings.ollama_timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

                # Record usage
                if "prompt_eval_count" in data or "eval_count" in data:
                    record_usage(
                        provider="ollama",
                        model=self.model,
                        prompt_tokens=data.get("prompt_eval_count", 0),
                        completion_tokens=data.get("eval_count", 0),
                    )

                return data
        except httpx.HTTPStatusError as exc:
            raise ValueError(
                f"Ollama API 錯誤 ({exc.response.status_code}): {exc.response.reason_phrase}"
            ) from exc
        except httpx.RequestError as exc:
            raise ValueError(f"無法連線至 Ollama ({self.base_url}): {exc}") from exc

    async def _post_async(self, endpoint: str, payload: dict) -> dict:
        """Make POST request to Ollama API (Asynchronous)."""
        url = f"{self.base_url}{endpoint}"
        try:
            if self._async_client is not None:
                response = await self._async_client.post(url, json=payload, timeout=settings.ollama_timeout)
                response.raise_for_status()
                data = response.json()
            else:
                async with httpx.AsyncClient(timeout=settings.ollama_timeout) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    data = response.json()

            # Record usage
            if "prompt_eval_count" in data or "eval_count" in data:
                record_usage(
                    provider="ollama",
                    model=self.model,
                    prompt_tokens=data.get("prompt_eval_count", 0),
                    completion_tokens=data.get("eval_count", 0),
                )
            
            return data
        except httpx.HTTPStatusError as exc:
            raise ValueError(
                f"Ollama API 錯誤 ({exc.response.status_code}): {exc.response.reason_phrase}"
            ) from exc
        except httpx.RequestError as exc:
            raise ValueError(f"無法連線至 Ollama ({self.base_url}): {exc}") from exc

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
        """Translate blocks using Ollama API (Synchronous)."""
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
            "model": self.model,
            "format": "json",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }

        options = build_ollama_options()
        if options:
            payload["options"] = options

        response_data = self._post("/api/chat", payload)
        content = response_data.get("message", {}).get("content", "")

        if not content:
            raise ValueError("Ollama 回傳內容為空 (/api/chat)")

        result = safe_json_loads(content)
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
        """Translate blocks using Ollama API (Asynchronous)."""
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
            "model": self.model,
            "format": "json",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }

        options = build_ollama_options()
        if options:
            payload["options"] = options

        response_data = await self._post_async("/api/chat", payload)
        content = response_data.get("message", {}).get("content", "")

        if not content:
            raise ValueError("Ollama 回傳內容為空 (/api/chat)")

        result = safe_json_loads(content)
        validate_contract(result)
        return result

    def _get_system_message(self) -> str:
        try:
            return get_prompt("system_message")
        except FileNotFoundError:
            return "你是負責翻譯 PPTX 文字區塊的助手。只回傳 JSON，且必須符合既定 schema。"

    def translate_plain(self, prompt: str) -> str:
        """Translate using plain text prompt (Synchronous)."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        options = build_ollama_options()
        if options:
            payload["options"] = options
        response_data = self._post("/api/generate", payload)
        content = response_data.get("response", "")
        if not content:
            raise ValueError("Ollama 回傳內容為空 (/api/generate)")
        return content

    async def translate_plain_async(self, prompt: str) -> str:
        """Translate using plain text prompt (Asynchronous)."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        options = build_ollama_options()
        if options:
            payload["options"] = options
        response_data = await self._post_async("/api/generate", payload)
        content = response_data.get("response", "")
        if not content:
            raise ValueError("Ollama 回傳內容為空 (/api/generate)")
        return content
