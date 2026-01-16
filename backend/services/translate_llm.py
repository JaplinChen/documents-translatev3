from __future__ import annotations

import logging
import os
import random
import re
import time
from urllib.error import HTTPError

from backend.services.llm_clients import (
    GeminiTranslator,
    MockTranslator,
    OllamaTranslator,
    OpenAITranslator,
    TranslationConfig,
)
from backend.services.llm_contract import build_contract, coerce_contract, validate_contract
from backend.services.llm_context import build_context
from backend.services.llm_glossary import apply_glossary, load_glossary
from backend.services.llm_placeholders import apply_placeholders, has_placeholder, restore_placeholders
from backend.services.llm_utils import cache_key, chunked, tm_respects_terms
from backend.services.language_detect import detect_language
from backend.services.prompt_store import render_prompt
from backend.services.translation_memory import (
    get_glossary_terms,
    get_glossary_terms_any,
    get_tm_terms,
    get_tm_terms_any,
    lookup_tm,
    save_tm,
)

LOGGER = logging.getLogger(__name__)


_LANGUAGE_LABELS = {
    "zh-TW": "Traditional Chinese (zh-TW)",
    "zh-CN": "Simplified Chinese (zh-CN)",
    "zh": "Chinese (zh)",
    "vi": "Vietnamese (vi)",
    "en": "English (en)",
    "ja": "Japanese (ja)",
    "ko": "Korean (ko)",
}

_LANGUAGE_HINTS = {
    "vi": (
        "IMPORTANT: You MUST output Vietnamese (Tiếng Việt) ONLY.\n"
        "Use proper Vietnamese diacritics (ă, â, ê, ô, ơ, ư, đ).\n"
        "Examples: 解決方案 → Giải pháp (NOT Solusyon), 自動 → Tự động.\n"
        "DO NOT output Tagalog, Filipino, Spanish, or English."
    ),
    "zh-TW": "\u8acb\u4f7f\u7528\u7e41\u9ad4\u4e2d\u6587\u3002",
    "zh-CN": "\u8acb\u4f7f\u7528\u7c21\u9ad4\u4e2d\u6587\u3002",
    "zh": "\u8acb\u4f7f\u7528\u4e2d\u6587\u3002",
    "en": "Please respond in English.",
    "ja": "\u65e5\u672c\u8a9e\u3067\u56de\u7b54\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
    "ko": "\ud55c\uad6d\uc5b4\ub85c \ub2f5\ud574\uc8fc\uc138\uc694\u3002",
}

# Few-shot examples to force correct language output (especially for Vietnamese)
_LANGUAGE_EXAMPLES = {
    "vi": (
        "<<<BLOCK:0>>>\n"
        "Giải pháp doanh nghiệp\n"
        "<<<END>>>"
    ),
    "zh-TW": (
        "<<<BLOCK:0>>>\n"
        "企業解決方案\n"
        "<<<END>>>"
    ),
    "zh-CN": (
        "<<<BLOCK:0>>>\n"
        "企业解决方案\n"
        "<<<END>>>"
    ),
    "en": (
        "<<<BLOCK:0>>>\n"
        "Enterprise Solution\n"
        "<<<END>>>"
    ),
    "ja": (
        "<<<BLOCK:0>>>\n"
        "企業ソリューション\n"
        "<<<END>>>"
    ),
    "ko": (
        "<<<BLOCK:0>>>\n"
        "기업 솔루션\n"
        "<<<END>>>"
    ),
}


def _language_example(code: str) -> str:
    normalized = (code or "").strip()
    return _LANGUAGE_EXAMPLES.get(normalized, "")


def _language_label(code: str) -> str:
    normalized = (code or "").strip()
    return _LANGUAGE_LABELS.get(normalized, normalized or code)


def _language_hint(code: str) -> str:
    normalized = (code or "").strip()
    return _LANGUAGE_HINTS.get(normalized, "")


def _build_ollama_batch_prompt(
    blocks: list[dict], target_language: str, strict: bool = False
) -> str:
    label = _language_label(target_language)
    hint = _language_hint(target_language)
    example = _language_example(target_language)
    language_guard = (
        "Every line MUST be in the target language. Verify language consistency."
        if strict
        else "Every line MUST be in the target language."
    )
    blocks_lines: list[str] = []
    for idx, block in enumerate(blocks):
        blocks_lines.append(f"<<<BLOCK:{idx}>>>")
        blocks_lines.append(block.get("source_text", ""))
        blocks_lines.append("<<<END>>>")
        blocks_lines.append("")
    blocks_text = "\n".join(blocks_lines).strip()
    try:
        return render_prompt(
            "ollama_batch",
            {
                "target_language_label": label,
                "target_language_code": target_language,
                "language_guard": language_guard,
                "language_hint": hint,
                "language_example": example,
                "blocks": blocks_text,
            },
        )
    except FileNotFoundError:
        parts = [
            "請將每個區塊翻譯為目標語言。",
            f"目標語言：{label}",
            f"目標語言代碼：{target_language}",
            hint,
            language_guard,
            "請保留標記並只輸出翻譯文字。",
            "格式：",
            "<<<BLOCK:0>>>",
            "<翻譯文字>",
            "<<<END>>>",
            "",
            "輸入：",
            blocks_text,
        ]
        return "\n".join(parts)


def _parse_ollama_batch_response(text: str, count: int) -> list[str] | None:
    pattern = re.compile(r"<<<BLOCK:(\d+)>>>\n(.*?)\n<<<END>>>", re.DOTALL)
    matches = pattern.findall(text)
    if not matches:
        return None
    translated = [""] * count
    for idx_str, content in matches:
        try:
            idx = int(idx_str)
        except ValueError:
            continue
        if 0 <= idx < count:
            translated[idx] = content.strip()
    if any(item == "" for item in translated):
        return None
    return translated


def _matches_target_language(text: str, target_language: str) -> bool:
    cleaned = (text or "").strip()
    if not cleaned:
        return True
    detected = detect_language(cleaned)
    if not detected:
        return True
    target = (target_language or "").strip()
    if not target:
        return True
    if target.startswith("zh-"):
        return detected == target
    if target == "zh":
        return detected.startswith("zh")
    return detected == target


def _has_language_mismatch(texts: list[str], target_language: str) -> bool:
    if not target_language or target_language == "auto":
        return False
    return any(not _matches_target_language(text, target_language) for text in texts)


def _build_language_retry_context(
    context: dict | None, texts: list[str], target_language: str
) -> dict:
    updated = dict(context or {})
    detected_counts: dict[str, int] = {}
    for text in texts:
        detected = detect_language((text or "").strip())
        if detected:
            detected_counts[detected] = detected_counts.get(detected, 0) + 1
    detected_top = (
        sorted(detected_counts.items(), key=lambda item: item[1], reverse=True)[0][0]
        if detected_counts
        else None
    )
    updated["language_guard"] = (
        f"上一輪輸出偵測語言為 {detected_top}，不符合目標語言 {target_language}。"
        "請重新翻譯並確保每個 translated_text 都是目標語言。"
    )
    hint = _language_hint(target_language)
    if hint:
        updated["language_hint"] = hint
    return updated


def translate_blocks(
    blocks: list[dict] | tuple[dict, ...],
    target_language: str,
    use_tm: bool = True,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> dict:
    mode = os.getenv("TRANSLATE_LLM_MODE", "real").lower()
    fallback_on_error = os.getenv("LLM_FALLBACK_ON_ERROR", "0").lower() in {
        "1",
        "true",
        "yes",
    }

    if mode == "mock":
        resolved_provider = "mock"
        translator = MockTranslator()
    else:
        resolved_provider = (provider or "openai").lower()
        if resolved_provider in {"openai", "chatgpt", "gpt-4o"}:
            resolved_key = api_key or os.getenv("OPENAI_API_KEY", "")
            if not resolved_key:
                if fallback_on_error:
                    translator = MockTranslator()
                else:
                    raise EnvironmentError("OPENAI_API_KEY is required for OpenAI translation")
            else:
                model_name = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                if resolved_provider == "gpt-4o" and not model:
                    model_name = "gpt-4o"
                config = TranslationConfig(
                    model=model_name,
                    api_key=resolved_key,
                    base_url=base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                )
                translator = OpenAITranslator(config)
        elif resolved_provider == "gemini":
            resolved_key = api_key or os.getenv("GEMINI_API_KEY", "")
            if not resolved_key:
                if fallback_on_error:
                    translator = MockTranslator()
                else:
                    raise EnvironmentError("GEMINI_API_KEY is required for Gemini translation")
            else:
                translator = GeminiTranslator(
                    api_key=resolved_key,
                    base_url=base_url
                    or os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"),
                    model=model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
                )
        elif resolved_provider == "ollama":
            resolved_model = model or os.getenv("OLLAMA_MODEL", "llama3.1")
            translator = OllamaTranslator(
                model=resolved_model,
                base_url=base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            )
        else:
            translator = MockTranslator()

    blocks_list = list(blocks)
    cache: dict[str, str] = {}
    translated_texts: list[str | None] = [None] * len(blocks_list)
    pending: list[tuple[int, dict]] = []
    source_lang = os.getenv("SOURCE_LANGUAGE", "auto")
    preferred_terms: list[tuple[str, str]] = []
    if source_lang and source_lang != "auto":
        preferred_terms = get_glossary_terms(source_lang, target_language)
        if use_tm:
            preferred_terms.extend(get_tm_terms(source_lang, target_language))
    else:
        preferred_terms = get_glossary_terms_any(target_language)
        if use_tm:
            preferred_terms.extend(get_tm_terms_any(target_language))

    use_placeholders = resolved_provider != "ollama"

    for index, block in enumerate(blocks_list):
        key = cache_key(block)
        if not key:
            translated_texts[index] = ""
            continue
        if key in cache:
            if not use_placeholders and has_placeholder(cache[key]):
                continue
            translated_texts[index] = cache[key]
            continue
        if source_lang and source_lang != "auto":
            if use_tm:
                tm_hit = lookup_tm(
                    source_lang=source_lang,
                    target_lang=target_language,
                    text=key,
                )
                if (
                    tm_hit is not None
                    and tm_respects_terms(key, tm_hit, preferred_terms)
                    and not (not use_placeholders and has_placeholder(tm_hit))
                ):
                    translated_texts[index] = tm_hit
                    cache[key] = tm_hit
                    continue
        pending.append((index, block))

    single_request = os.getenv("LLM_SINGLE_REQUEST", "1").lower() in {"1", "true", "yes"}
    chunk_size = int(os.getenv("LLM_CHUNK_SIZE", "40"))
    if resolved_provider == "ollama" and "LLM_CHUNK_SIZE" not in os.environ:
        chunk_size = 6  # 平衡穩定性與效能，減少 API 呼叫次數
    if resolved_provider == "gemini" and "LLM_CHUNK_SIZE" not in os.environ:
        chunk_size = 4
    max_retries = int(os.getenv("LLM_MAX_RETRIES", "2"))
    if resolved_provider == "ollama" and "LLM_MAX_RETRIES" not in os.environ:
        max_retries = 1
    if resolved_provider == "gemini" and "LLM_MAX_RETRIES" not in os.environ:
        max_retries = 2
    backoff = float(os.getenv("LLM_RETRY_BACKOFF", "0.8"))
    max_backoff = float(os.getenv("LLM_RETRY_MAX_BACKOFF", "8"))
    context_strategy = os.getenv("LLM_CONTEXT_STRATEGY", "none").lower()
    glossary_path = os.getenv("LLM_GLOSSARY_PATH", "")
    glossary = load_glossary(glossary_path)
    chunk_delay = float(os.getenv("LLM_CHUNK_DELAY", "0"))
    if resolved_provider == "gemini" and "LLM_CHUNK_DELAY" not in os.environ:
        chunk_delay = 1.0
    if resolved_provider == "ollama" and "LLM_SINGLE_REQUEST" not in os.environ:
        single_request = False
    if single_request:
        chunk_size = len(pending) if pending else chunk_size
        chunk_delay = 0.0

    LOGGER.info(
        "LLM translate start provider=%s model=%s blocks=%s chunk=%s retries=%s backoff=%.2f placeholders=%s single=%s",
        resolved_provider,
        model or "",
        len(blocks_list),
        chunk_size,
        max_retries,
        backoff,
        use_placeholders,
        single_request,
    )

    prompt_language = target_language
    for chunk_index, chunk in enumerate(chunked(pending, chunk_size), start=1):
        chunk_started = time.perf_counter()
        chunk_blocks = []
        placeholder_maps: list[dict[str, str]] = []
        placeholder_tokens: list[str] = []
        for _, block in chunk:
            prepared = dict(block)
            if use_placeholders:
                prepared_text, mapping = apply_placeholders(
                    prepared.get("source_text", ""), preferred_terms
                )
            else:
                prepared_text = prepared.get("source_text", "")
                mapping = {}
            prepared["source_text"] = prepared_text
            if mapping:
                placeholder_tokens.extend(mapping.keys())
            placeholder_maps.append(mapping)
            chunk_blocks.append(prepared)
        context = build_context(context_strategy, blocks_list, chunk_blocks)
        attempt = 0
        retried_for_language = False
        while True:
            try:
                attempt += 1
                attempt_started = time.perf_counter()
                LOGGER.info(
                    "LLM chunk %s attempt %s size=%s context=%s",
                    chunk_index,
                    attempt,
                    len(chunk_blocks),
                    context_strategy,
                )
                if resolved_provider == "ollama":
                    prompt = _build_ollama_batch_prompt(chunk_blocks, prompt_language)
                    text_output = translator.translate_plain(prompt)
                    translated_texts_chunk = _parse_ollama_batch_response(
                        text_output, len(chunk_blocks)
                    )
                    if translated_texts_chunk is None:
                        LOGGER.warning("Ollama response format mismatch, fallback to JSON mode")
                        result = translator.translate(
                            chunk_blocks,
                            prompt_language,
                            context=context,
                            preferred_terms=preferred_terms,
                            placeholder_tokens=placeholder_tokens,
                        )
                        result = coerce_contract(result, chunk_blocks, target_language)
                        validate_contract(result)
                    else:
                        result = build_contract(
                            chunk_blocks, target_language, translated_texts_chunk
                        )
                        validate_contract(result)
                else:
                    result = translator.translate(
                        chunk_blocks,
                        prompt_language,
                        context=context,
                        preferred_terms=preferred_terms,
                        placeholder_tokens=placeholder_tokens,
                    )
                    result = coerce_contract(result, chunk_blocks, target_language)
                    validate_contract(result)

                chunk_texts = [item.get("translated_text", "") for item in result["blocks"]]
                if not retried_for_language and _has_language_mismatch(
                    chunk_texts, target_language
                ):
                    retried_for_language = True
                    LOGGER.warning(
                        "LLM chunk %s language mismatch detected; retrying once",
                        chunk_index,
                    )
                    if resolved_provider == "ollama":
                        strict_prompt = _build_ollama_batch_prompt(
                            chunk_blocks, prompt_language, strict=True
                        )
                        strict_output = translator.translate_plain(strict_prompt)
                        strict_texts = _parse_ollama_batch_response(
                            strict_output, len(chunk_blocks)
                        )
                        if strict_texts is not None:
                            result = build_contract(
                                chunk_blocks, target_language, strict_texts
                            )
                            validate_contract(result)
                        else:
                            # strict retry 格式不符時，不再繼續使用錯誤結果
                            LOGGER.error(
                                "Ollama strict retry format mismatch and language still incorrect"
                            )
                            raise ValueError(
                                "Ollama 重試後格式不符且語言仍不正確。"
                                f"目標語言={target_language}。"
                                "請改用其他模型或供應商。"
                            )
                    else:
                        strict_context = _build_language_retry_context(
                            context, chunk_texts, target_language
                        )
                        result = translator.translate(
                            chunk_blocks,
                            prompt_language,
                            context=strict_context,
                            preferred_terms=preferred_terms,
                            placeholder_tokens=placeholder_tokens,
                        )
                        result = coerce_contract(result, chunk_blocks, target_language)
                        validate_contract(result)
                        strict_texts = [
                            item.get("translated_text", "") for item in result["blocks"]
                        ]
                        if _has_language_mismatch(strict_texts, target_language):
                            LOGGER.warning(
                                "LLM chunk %s strict retry still mismatched target_language=%s",
                                chunk_index,
                                target_language,
                            )
                    post_retry_texts = [
                        item.get("translated_text", "") for item in result["blocks"]
                    ]
                    if _has_language_mismatch(post_retry_texts, target_language):
                        detected_counts: dict[str, int] = {}
                        for text in post_retry_texts:
                            detected = detect_language((text or "").strip())
                            if detected:
                                detected_counts[detected] = detected_counts.get(detected, 0) + 1
                        detected_top = (
                            sorted(
                                detected_counts.items(),
                                key=lambda item: item[1],
                                reverse=True,
                            )[0][0]
                            if detected_counts
                            else None
                        )
                        raise ValueError(
                            "翻譯結果不符合目標語言，已重試仍失敗。"
                            f"目標語言={target_language}，偵測語言={detected_top or 'unknown'}。"
                            "請改用其他模型/供應商或再重試一次。"
                        )
                for (original, mapping), translated in zip(
                    zip(chunk, placeholder_maps), result["blocks"]
                ):
                    if "client_id" not in translated and original[1].get("client_id"):
                        translated["client_id"] = original[1].get("client_id")
                    translated_text = translated.get("translated_text", "")
                    translated_text = restore_placeholders(translated_text, mapping)
                    if glossary:
                        translated_text = apply_glossary(translated_text, glossary)
                    translated_texts[original[0]] = translated_text
                    if (
                        use_tm
                        and not has_placeholder(translated_text)
                        and _matches_target_language(translated_text, target_language)
                    ):
                        cache[cache_key(original[1])] = translated_text
                        save_tm(
                            source_lang=os.getenv("SOURCE_LANGUAGE", "auto"),
                            target_lang=target_language,
                            text=cache_key(original[1]),
                            translated=translated_text,
                        )
                break
            except Exception as exc:
                duration = time.perf_counter() - attempt_started
                error_msg = str(exc)

                if "image" in error_msg.lower() or "vision" in error_msg.lower():
                    LOGGER.error(
                        "LLM 翻譯失敗：偵測到圖片相關錯誤，所選模型可能不支援圖片輸入。錯誤：%s",
                        error_msg,
                    )
                    raise ValueError(
                        "偵測到圖片相關錯誤。您的 PPTX 可能包含圖片，但目前所選模型不支援圖片輸入。"
                        "請在 LLM 設定中選擇支援視覺模型（例如 GPT-4o）。"
                    ) from exc

                LOGGER.warning(
                    "LLM chunk %s attempt %s failed in %.2fs: %s",
                    chunk_index,
                    attempt,
                    duration,
                    exc,
                )
                if attempt > max_retries:
                    if fallback_on_error and mode != "mock":
                        LOGGER.warning(
                            "LLM chunk %s fallback to mock after %s attempts",
                            chunk_index,
                            attempt,
                        )
                        result = MockTranslator().translate(
                            chunk_blocks,
                            target_language,
                            context=context,
                            preferred_terms=preferred_terms,
                            placeholder_tokens=placeholder_tokens,
                        )
                        result = coerce_contract(result, chunk_blocks, target_language)
                        validate_contract(result)
                        for (original, mapping), translated in zip(
                            zip(chunk, placeholder_maps), result["blocks"]
                        ):
                            if "client_id" not in translated and original[1].get("client_id"):
                                translated["client_id"] = original[1].get("client_id")
                            translated_text = translated.get("translated_text", "")
                            translated_text = restore_placeholders(translated_text, mapping)
                            if glossary:
                                translated_text = apply_glossary(translated_text, glossary)
                            translated_texts[original[0]] = translated_text
                            if (
                                use_tm
                                and not has_placeholder(translated_text)
                                and _matches_target_language(translated_text, target_language)
                            ):
                                cache[cache_key(original[1])] = translated_text
                                save_tm(
                                    source_lang=os.getenv("SOURCE_LANGUAGE", "auto"),
                                    target_lang=target_language,
                                    text=cache_key(original[1]),
                                    translated=translated_text,
                                )
                        break
                    raise
                retry_after = None
                if isinstance(exc, HTTPError):
                    if exc.code in {429, 503}:
                        retry_after = exc.headers.get("Retry-After")
                if retry_after:
                    try:
                        sleep_for = max(float(retry_after), 0)
                    except ValueError:
                        sleep_for = backoff * attempt
                else:
                    sleep_for = min(backoff * attempt, max_backoff) + random.uniform(0, 0.5)
                time.sleep(sleep_for)
        chunk_duration = time.perf_counter() - chunk_started
        LOGGER.info("LLM chunk %s completed in %.2fs", chunk_index, chunk_duration)
        if chunk_delay:
            time.sleep(chunk_delay)

    final_texts = [text if text is not None else "" for text in translated_texts]
    return build_contract(
        blocks=blocks_list,
        translated_texts=final_texts,
        target_language=target_language,
    )
