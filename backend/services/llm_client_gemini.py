"""Google Gemini API client for translation.

This module provides the GeminiTranslator class with comprehensive
error handling for Gemini's REST API.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable

import httpx

from backend.config import settings
from backend.services.llm_client_base import load_contract_example
from backend.services.llm_contract import validate_contract
from backend.services.llm_prompt import build_prompt
from backend.services.llm_utils import safe_json_loads

LOGGER = logging.getLogger(__name__)


class GeminiTranslator:
    """Translator using Google Gemini's REST API."""

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

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
        """Translate blocks using Gemini API (Synchronous)."""
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
        full_prompt = f"{system_message}\n\n[TASK START]\n{prompt}"

        payload = {
            "contents": [{"role": "user", "parts": [{"text": full_prompt}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        }

        timeout = settings.gemini_timeout
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                response_data = response.json()
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc)
        except httpx.RequestError as exc:
            raise ValueError(f"Gemini API 連線錯誤: {exc}") from exc

        return self._process_response(response_data)

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
        """Translate blocks using Gemini API (Asynchronous)."""
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
        full_prompt = f"{system_message}\n\n[TASK START]\n{prompt}"
        
        payload = {
            "contents": [{"role": "user", "parts": [{"text": full_prompt}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        }

        timeout = settings.gemini_timeout
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                response_data = response.json()
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc)
        except httpx.RequestError as exc:
            raise ValueError(f"Gemini API 連線錯誤: {exc}") from exc

        return self._process_response(response_data)

    def _process_response(self, response_data: dict) -> dict:
        """Extract and validate translation from Gemini response."""
        self._check_prompt_feedback(response_data)
        self._check_candidates(response_data)

        parts = response_data.get("candidates", [])[0].get("content", {}).get("parts", [])
        content = parts[0].get("text", "") if parts else ""

        if not content:
            raise ValueError("Gemini 回應內容為空。請檢查 API 設定或稍後再試。")

        result = safe_json_loads(content)
        validate_contract(result)
        return result

    def _handle_http_error(self, exc: httpx.HTTPStatusError) -> None:
        """Handle HTTP errors from Gemini API."""
        response = exc.response
        error_message = response.text
        try:
            error_json = response.json()
            error_message = error_json.get("error", {}).get("message", response.text)
        except (json.JSONDecodeError, ValueError):
            pass

        code = response.status_code
        if code == 400:
            raise ValueError(f"Gemini API 請求錯誤 (400): {error_message}") from exc
        elif code == 403:
            raise ValueError(f"Gemini API 權限不足 (403): {error_message}") from exc
        elif code == 429:
            raise ValueError(f"Gemini API 請求過於頻繁 (429): {error_message}") from exc
        elif code >= 500:
            raise ValueError(f"Gemini 伺服器錯誤 ({code}): {error_message}") from exc
        raise ValueError(f"Gemini API 錯誤 ({code}): {error_message}") from exc

    def _check_prompt_feedback(self, response_data: dict) -> None:
        """Check for prompt blocking in response."""
        prompt_feedback = response_data.get("promptFeedback", {})
        block_reason = prompt_feedback.get("blockReason")

        if block_reason:
            safety_ratings = prompt_feedback.get("safetyRatings", [])
            blocked_categories = [
                r.get("category", "") for r in safety_ratings if r.get("blocked", False)
            ]
            raise ValueError(
                f"Gemini 拒絕處理此請求 (blockReason={block_reason})。"
                f"被封鎖的分類：{', '.join(blocked_categories) or '未知'}。"
            )

    def _check_candidates(self, response_data: dict) -> None:
        """Check candidates and finish reason in response."""
        candidates = response_data.get("candidates", [])
        if not candidates:
            raise ValueError("Gemini 未回傳任何結果 (candidates 為空)。")

        finish_reason = candidates[0].get("finishReason", "")
        if finish_reason == "SAFETY":
            raise ValueError("Gemini 因安全政策停止生成 (finishReason=SAFETY)。")
        elif finish_reason == "RECITATION":
            raise ValueError("Gemini 因可能涉及版權內容停止生成 (finishReason=RECITATION)。")
        elif finish_reason == "MAX_TOKENS":
            raise ValueError("Gemini 輸出超過 token 上限 (finishReason=MAX_TOKENS)。")

    def complete(self, prompt: str) -> str:
        """Complete a prompt using Gemini API (Synchronous)."""
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0},
        }
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        with httpx.Client(timeout=settings.gemini_timeout) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            response_data = response.json()
        parts = response_data.get("candidates", [])[0].get("content", {}).get("parts", [])
        return parts[0].get("text", "") if parts else ""

    async def complete_async(self, prompt: str) -> str:
        """Complete a prompt using Gemini API (Asynchronous)."""
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0},
        }
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        async with httpx.AsyncClient(timeout=settings.gemini_timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            response_data = response.json()
        parts = response_data.get("candidates", [])[0].get("content", {}).get("parts", [])
        return parts[0].get("text", "") if parts else ""
