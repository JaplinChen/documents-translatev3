"""Translation retry helpers.

Handles language mismatch detection, retry context building, and
result post-processing.
"""

from __future__ import annotations

from backend.services.language_detect import (
    _CJK_RE,
    _VI_DIACRITIC_RE,
    detect_language,
)
from backend.services.llm_glossary import apply_glossary
from backend.services.llm_placeholders import (
    has_placeholder,
    restore_placeholders,
)
from backend.services.llm_utils import cache_key
from backend.services.translate_config import get_language_hint
from backend.services.translation_memory import save_tm

def matches_target_language(text: str, target_language: str) -> bool:
    """Return True when the detected language matches the expectation."""
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


def has_language_mismatch(texts: list[str], target_language: str) -> bool:
    """Return True if majority of texts do not match the target language."""
    if not target_language or target_language == "auto":
        return False
    if not texts:
        return False

    total = len(texts)
    threshold = total * 0.5
    matching_count = 0
    for text in texts:
        if matches_target_language(text, target_language):
            matching_count += 1
            if matching_count >= threshold:
                return False
    return matching_count < threshold


def build_language_retry_context(
    context: dict | None, texts: list[str], target_language: str
) -> dict:
    """Build context payload when LLM outputs the wrong language."""
    updated = dict(context or {})
    detected_counts: dict[str, int] = {}
    for text in texts:
        detected = detect_language((text or "").strip())
        if detected:
            detected_counts[detected] = detected_counts.get(detected, 0) + 1

    detected_top = (
        max(detected_counts.items(), key=lambda item: item[1])[0]
        if detected_counts
        else None
    )
    updated["language_guard"] = (
        f"上一輪輸出偵測語言為 {detected_top}，不符合目標語言 {target_language}。"
        "請重新翻譯並確保每個 translated_text 都是目標語言。"
    )
    hint = get_language_hint(target_language)
    if hint:
        updated["language_hint"] = hint
    return updated


def _apply_vi_preservation(source_text: str, translated_text: str) -> str:
    src_vi_parts = _VI_DIACRITIC_RE.findall(source_text)
    if len(src_vi_parts) < 2:
        return translated_text

    if _VI_DIACRITIC_RE.search(translated_text):
        return translated_text

    cjk_match = _CJK_RE.search(source_text)
    vi_prefix = (
        source_text[:cjk_match.start()].strip()
        if cjk_match
        else source_text
    )
    if vi_prefix and vi_prefix not in translated_text:
        return f"{vi_prefix} {translated_text}"
    return translated_text


def _should_save_tm(
    translated_text: str, target_language: str, use_tm: bool
) -> bool:
    return (
        use_tm
        and not has_placeholder(translated_text)
        and matches_target_language(translated_text, target_language)
    )


def apply_translation_results(
    chunk: list[tuple[int, dict]],
    placeholder_maps: list[dict[str, str]],
    result: dict,
    translated_texts: list[str | None],
    cache: dict[str, str],
    glossary: dict | None,
    target_language: str,
    use_tm: bool,
    llm_context: dict | None = None,
) -> None:
    """Restore placeholders, apply glossary, and optionally save to TM."""
    from backend.config import settings

    for (original, mapping), translated in zip(
        zip(chunk, placeholder_maps, strict=True),
        result["blocks"],
        strict=True,
    ):
        if "client_id" not in translated and original[1].get("client_id"):
            translated["client_id"] = original[1].get("client_id")

        translated_text = translated.get("translated_text", "")
        translated_text = restore_placeholders(translated_text, mapping)

        source_text = original[1].get("source_text", "").strip()
        translated_text = _apply_vi_preservation(source_text, translated_text)

        if glossary:
            translated_text = apply_glossary(translated_text, glossary)

        translated_texts[original[0]] = translated_text
        key = cache_key(original[1], context=llm_context)

        if _should_save_tm(translated_text, target_language, use_tm):
            cache[key] = translated_text
            save_tm(
                source_lang=settings.source_language
                if settings.source_language != "auto"
                else "unknown",
                target_lang=target_language,
                text=source_text,
                translated=translated_text,
                context=llm_context,
            )


def retry_for_language(
    translator,
    provider,
    chunk_blocks,
    target_language,
    context,
    preferred_terms,
    placeholder_tokens,
    chunk_texts,
):
    """Retry translation synchronously with stricter language guard."""
    from backend.services.llm_contract import (
        build_contract,
        coerce_contract,
        validate_contract,
    )
    from backend.services.translate_prompt import (
        build_ollama_batch_prompt,
        parse_ollama_batch_response,
    )

    if provider == "ollama":
        strict_prompt = build_ollama_batch_prompt(
            chunk_blocks, target_language, strict=True
        )
        strict_output = translator.translate_plain(strict_prompt)
        strict_texts = parse_ollama_batch_response(
            strict_output, len(chunk_blocks)
        )
        if strict_texts is not None:
            result = build_contract(
                chunk_blocks,
                target_language,
                strict_texts,
            )
            validate_contract(result)
            return result
        raise ValueError("Ollama 重試語言失敗")

    strict_context = build_language_retry_context(
        context, chunk_texts, target_language
    )
    result = translator.translate(
        chunk_blocks,
        target_language,
        context=strict_context,
        preferred_terms=preferred_terms,
        placeholder_tokens=placeholder_tokens,
    )
    result = coerce_contract(result, chunk_blocks, target_language)
    validate_contract(result)

    new_texts = [
        item.get("translated_text", "")
        for item in result["blocks"]
    ]
    if has_language_mismatch(new_texts, target_language):
        raise ValueError(
            f"重試翻譯後語言仍不符合目標語言 ({target_language})"
        )

    return result


async def retry_for_language_async(
    translator,
    provider,
    chunk_blocks,
    target_language,
    context,
    preferred_terms,
    placeholder_tokens,
    chunk_texts,
):
    """Retry translation asynchronously with stricter language guard."""
    from backend.services.llm_contract import (
        build_contract,
        coerce_contract,
        validate_contract,
    )
    from backend.services.translate_prompt import (
        build_ollama_batch_prompt,
        parse_ollama_batch_response,
    )

    if provider == "ollama":
        strict_prompt = build_ollama_batch_prompt(
            chunk_blocks, target_language, strict=True
        )
        strict_output = await translator.translate_plain_async(strict_prompt)
        strict_texts = parse_ollama_batch_response(
            strict_output, len(chunk_blocks)
        )
        if strict_texts is not None:
            result = build_contract(
                chunk_blocks,
                target_language,
                strict_texts,
            )
            validate_contract(result)
            return result
        raise ValueError("Ollama 重試語言失敗 (async)")

    strict_context = build_language_retry_context(
        context, chunk_texts, target_language
    )
    result = await translator.translate_async(
        chunk_blocks,
        target_language,
        context=strict_context,
        preferred_terms=preferred_terms,
        placeholder_tokens=placeholder_tokens,
    )
    result = coerce_contract(result, chunk_blocks, target_language)
    validate_contract(result)

    new_texts = [
        item.get("translated_text", "")
        for item in result["blocks"]
    ]
    if has_language_mismatch(new_texts, target_language):
        raise ValueError(
            f"重試翻譯後語言仍不符合目標語言 ({target_language})"
        )

    return result


def fallback_mock(
    chunk_blocks,
    target_language,
    context,
    preferred_terms,
    placeholder_tokens,
):
    """Fallback translator for offline/local runs."""
    from backend.services.llm_clients import MockTranslator
    from backend.services.llm_contract import (
        coerce_contract,
        validate_contract,
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
    return result


async def fallback_mock_async(
    chunk_blocks,
    target_language,
    context,
    preferred_terms,
    placeholder_tokens,
):
    """Async fallback translator for offline/local runs."""
    from backend.services.llm_clients import MockTranslator
    from backend.services.llm_contract import (
        coerce_contract,
        validate_contract,
    )

    result = await MockTranslator().translate_async(
        chunk_blocks,
        target_language,
        context=context,
        preferred_terms=preferred_terms,
        placeholder_tokens=placeholder_tokens,
    )
    result = coerce_contract(result, chunk_blocks, target_language)
    validate_contract(result)
    return result
