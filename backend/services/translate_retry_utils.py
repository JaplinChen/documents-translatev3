from __future__ import annotations

from backend.services.language_detect import (
    _CJK_RE,
    _VI_DIACRITIC_RE,
    detect_language,
)
from backend.services.translate_config import get_language_hint


def matches_target_language(text: str, target_language: str) -> bool:
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


def apply_vi_preservation(
    source_text: str,
    translated_text: str,
    target_language: str,
) -> str:
    if target_language != "vi":
        return translated_text
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


def should_save_tm(
    translated_text: str, target_language: str, use_tm: bool
) -> bool:
    from backend.services.llm_placeholders import has_placeholder

    return (
        not has_placeholder(translated_text)
        and matches_target_language(translated_text, target_language)
    )
