from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.request import Request, urlopen

from backend.services.llm_contract import build_contract, validate_contract
from backend.services.llm_prompt import build_prompt
from backend.services.prompt_store import get_prompt
from backend.services.llm_utils import safe_json_loads

CONTRACT_PATH = (
    Path(__file__).resolve().parents[2] / "docs" / "translation_contract_pptx.json"
)


def load_contract_example() -> dict:
    if not CONTRACT_PATH.exists():
        raise FileNotFoundError(f"Missing contract file: {CONTRACT_PATH}")
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class TranslationConfig:
    model: str
    api_key: str
    base_url: str


class MockTranslator:
    def translate(
        self,
        blocks: Iterable[dict],
        target_language: str,
        context: dict | None = None,
        preferred_terms: list[tuple[str, str]] | None = None,
        placeholder_tokens: list[str] | None = None,
    ) -> dict:
        return build_contract(blocks, target_language, translated_texts=None)


class OpenAITranslator:
    def __init__(self, config: TranslationConfig) -> None:
        self.config = config

    def translate(
        self,
        blocks: Iterable[dict],
        target_language: str,
        context: dict | None = None,
        preferred_terms: list[tuple[str, str]] | None = None,
        placeholder_tokens: list[str] | None = None,
    ) -> dict:
        contract_example = load_contract_example()
        prompt = build_prompt(
            blocks,
            target_language,
            contract_example,
            context,
            preferred_terms,
            placeholder_tokens,
        )
        try:
            system_message = get_prompt("system_message")
        except FileNotFoundError:
            system_message = (
                "你是負責翻譯 PPTX 文字區塊的助手。"
                "只回傳 JSON，且必須符合既定 schema。"
            )
        payload = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_message,
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        data = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.config.base_url}/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        timeout = float(os.getenv("OPENAI_TIMEOUT", "60"))
        with urlopen(request, timeout=timeout) as response:
            response_data = json.loads(response.read().decode("utf-8"))
        content = response_data["choices"][0]["message"]["content"]
        result = json.loads(content)
        validate_contract(result)
        return result


class GeminiTranslator:
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
    ) -> dict:
        from urllib.error import HTTPError, URLError
        import socket

        contract_example = load_contract_example()
        prompt = build_prompt(
            blocks,
            target_language,
            contract_example,
            context,
            preferred_terms,
            placeholder_tokens,
        )
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            # Gemini REST API 使用 camelCase；responseMimeType 可要求回傳純 JSON。
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        }
        data = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        # Gemini 2.5 模型可能需要較長處理時間，預設 180 秒
        timeout = float(os.getenv("GEMINI_TIMEOUT", "180"))

        # 強化錯誤處理：捕捉 HTTP 錯誤、超時與解析 Gemini 錯誤回應
        try:
            with urlopen(request, timeout=timeout) as response:
                response_data = json.loads(response.read().decode("utf-8"))
        except (socket.timeout, TimeoutError) as timeout_err:
            raise ValueError(
                f"Gemini API 請求超時 ({timeout:.0f} 秒)。"
                "請嘗試以下方法：\n"
                "1. 設定環境變數 GEMINI_TIMEOUT=300 增加超時時間\n"
                "2. 設定 LLM_CHUNK_SIZE=2 減少每次翻譯的區塊數量\n"
                "3. 選擇較快的模型如 gemini-1.5-flash"
            ) from timeout_err
        except URLError as url_err:
            if isinstance(url_err.reason, (socket.timeout, TimeoutError)):
                raise ValueError(
                    f"Gemini API 連線超時 ({timeout:.0f} 秒)。"
                    "請檢查網路連線或稍後再試。"
                ) from url_err
            raise ValueError(
                f"Gemini API 網路錯誤: {url_err.reason}。"
                "請檢查網路連線或 API 端點設定。"
            ) from url_err
        except HTTPError as http_err:
            error_body = ""
            try:
                error_body = http_err.read().decode("utf-8")
                error_json = json.loads(error_body)
                error_message = error_json.get("error", {}).get("message", str(http_err))
            except (json.JSONDecodeError, UnicodeDecodeError):
                error_message = str(http_err)

            if http_err.code == 400:
                raise ValueError(
                    f"Gemini API 請求錯誤 (400): {error_message}。"
                    "請檢查 API Key 是否有效或模型名稱是否正確。"
                ) from http_err
            elif http_err.code == 403:
                raise ValueError(
                    f"Gemini API 權限不足 (403): {error_message}。"
                    "請確認 API Key 有權限存取此模型。"
                ) from http_err
            elif http_err.code == 429:
                raise ValueError(
                    f"Gemini API 請求過於頻繁 (429): {error_message}。"
                    "請稍後再試或調整 LLM_CHUNK_DELAY 設定。"
                ) from http_err
            elif http_err.code >= 500:
                raise ValueError(
                    f"Gemini 伺服器錯誤 ({http_err.code}): {error_message}。"
                    "請稍後再試。"
                ) from http_err
            else:
                raise ValueError(
                    f"Gemini API 錯誤 ({http_err.code}): {error_message}"
                ) from http_err

        # 檢查 promptFeedback.blockReason
        prompt_feedback = response_data.get("promptFeedback", {})
        block_reason = prompt_feedback.get("blockReason")
        if block_reason:
            safety_ratings = prompt_feedback.get("safetyRatings", [])
            blocked_categories = [
                r.get("category", "")
                for r in safety_ratings
                if r.get("blocked", False)
            ]
            raise ValueError(
                f"Gemini 拒絕處理此請求 (blockReason={block_reason})。"
                f"被封鎖的分類：{', '.join(blocked_categories) or '未知'}。"
                "請檢查 PPTX 內容是否包含敏感文字。"
            )

        candidates = response_data.get("candidates", [])
        if not candidates:
            raise ValueError(
                "Gemini 未回傳任何結果 (candidates 為空)。"
                "可能是內容被過濾或請求格式有誤。"
            )

        # 檢查 finishReason
        finish_reason = candidates[0].get("finishReason", "")
        if finish_reason == "SAFETY":
            safety_ratings = candidates[0].get("safetyRatings", [])
            high_risk = [
                r.get("category", "")
                for r in safety_ratings
                if r.get("probability", "") in ("HIGH", "MEDIUM")
            ]
            raise ValueError(
                f"Gemini 因安全政策停止生成 (finishReason=SAFETY)。"
                f"高風險分類：{', '.join(high_risk) or '未知'}。"
                "請檢查 PPTX 內容是否包含敏感文字。"
            )
        elif finish_reason == "RECITATION":
            raise ValueError(
                "Gemini 因可能涉及版權內容停止生成 (finishReason=RECITATION)。"
            )
        elif finish_reason == "MAX_TOKENS":
            raise ValueError(
                "Gemini 輸出超過 token 上限 (finishReason=MAX_TOKENS)。"
                "請嘗試減少每次翻譯的區塊數量 (調整 LLM_CHUNK_SIZE)。"
            )

        parts = candidates[0].get("content", {}).get("parts", [])
        content = parts[0].get("text", "") if parts else ""
        if not content:
            raise ValueError(
                "Gemini 回應內容為空。請檢查 API 設定或稍後再試。"
            )
        result = safe_json_loads(content)
        validate_contract(result)
        return result


def build_ollama_options() -> dict:
    options: dict[str, int] = {}
    num_gpu = os.getenv("OLLAMA_NUM_GPU")
    num_gpu_layers = os.getenv("OLLAMA_NUM_GPU_LAYERS")
    num_ctx = os.getenv("OLLAMA_NUM_CTX")
    num_thread = os.getenv("OLLAMA_NUM_THREAD")
    force_gpu = os.getenv("OLLAMA_FORCE_GPU", "").lower() in {"1", "true", "yes"}

    if num_gpu:
        try:
            options["num_gpu"] = int(num_gpu)
        except ValueError:
            pass
    if num_gpu_layers:
        try:
            options["num_gpu_layers"] = int(num_gpu_layers)
        except ValueError:
            pass
    if num_ctx:
        try:
            options["num_ctx"] = int(num_ctx)
        except ValueError:
            pass
    if num_thread:
        try:
            options["num_thread"] = int(num_thread)
        except ValueError:
            pass
    if force_gpu and "num_gpu" not in options and "num_gpu_layers" not in options:
        options["num_gpu"] = 1

    return options


class OllamaTranslator:
    def __init__(self, model: str, base_url: str) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = float(os.getenv("OLLAMA_TIMEOUT", "180"))

    def _post(self, endpoint: str, payload: dict) -> dict:
        import socket
        from urllib.error import HTTPError, URLError

        data = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.base_url}{endpoint}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (socket.timeout, TimeoutError) as timeout_err:
            raise ValueError(
                f"Ollama API 請求超時 ({self.timeout:.0f} 秒)。"
                "請嘗試增加 OLLAMA_TIMEOUT 或減少 LLM_CHUNK_SIZE。"
            ) from timeout_err
        except URLError as url_err:
            if isinstance(url_err.reason, (socket.timeout, TimeoutError)):
                raise ValueError(
                    f"Ollama API 連線超時 ({self.timeout:.0f} 秒)。"
                ) from url_err
            # 這是常見的 "Connection refused" 錯誤
            raise ValueError(
                f"無法連線至 Ollama ({self.base_url})。"
                "請確認 Ollama 已啟動且允許外部連線。"
            ) from url_err
        except HTTPError as http_err:
            raise ValueError(
                f"Ollama API 錯誤 ({http_err.code}): {http_err.reason}"
            ) from http_err

    def translate(
        self,
        blocks: Iterable[dict],
        target_language: str,
        context: dict | None = None,
        preferred_terms: list[tuple[str, str]] | None = None,
        placeholder_tokens: list[str] | None = None,
    ) -> dict:
        contract_example = load_contract_example()
        prompt = build_prompt(
            blocks,
            target_language,
            contract_example,
            context,
            preferred_terms,
            placeholder_tokens,
        )
        try:
            system_message = get_prompt("system_message")
        except FileNotFoundError:
            system_message = (
                "你是負責翻譯 PPTX 文字區塊的助手。"
                "只回傳 JSON，且必須符合既定 schema。"
            )
        payload = {
            "model": self.model,
            "format": "json",
            "messages": [
                {
                    "role": "system",
                    "content": system_message,
                },
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

    def translate_plain(self, prompt: str) -> str:
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
