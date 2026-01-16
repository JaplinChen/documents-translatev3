from __future__ import annotations

import json
from typing import Iterable

from backend.services.prompt_store import render_prompt

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
        "【重要】必須使用越南語（Tiếng Việt）翻譯。\n"
        "請使用正確的越南語字母與聲調符號（ă, â, ê, ô, ơ, ư, đ），例如：\n"
        "- 「解決方案」→ Giải pháp（不是 Solusyon）\n"
        "- 「自動」→ Tự động（不是 Automated）\n"
        "- 「影片」→ Video\n"
        "嚴禁輸出 Tagalog（菲律賓語）、Spanish、English 等其他語言。"
    ),
    "zh-TW": "請使用繁體中文。",
    "zh-CN": "請使用簡體中文。",
    "zh": "請使用中文。",
    "en": "Please respond in English.",
    "ja": "日本語で回答してください。",
    "ko": "한국어로 답해주세요。",
}


def _language_hint(code: str) -> str:
    return _LANGUAGE_HINTS.get((code or "").strip(), "")


def _language_label(code: str) -> str:
    normalized = (code or "").strip()
    return _LANGUAGE_LABELS.get(normalized, normalized or code)


def build_prompt(
    blocks: Iterable[dict],
    target_language: str,
    contract_example: dict,
    context: dict | None,
    preferred_terms: list[tuple[str, str]] | None = None,
    placeholder_tokens: list[str] | None = None,
) -> str:
    input_payload = {
        "target_language": target_language,
        "blocks": list(blocks),
        "contract_schema_example": contract_example,
    }
    if preferred_terms:
        input_payload["preferred_terms"] = [
            {"source": source, "target": target} for source, target in preferred_terms
        ]
    if placeholder_tokens:
        input_payload["placeholder_tokens"] = placeholder_tokens
    if context:
        input_payload["context"] = context
    payload = json.dumps(input_payload, ensure_ascii=False)
    try:
        return render_prompt(
            "translate_json",
            {
                "payload": payload,
                "language_hint": _language_hint(target_language),
                "target_language_label": _language_label(target_language),
                "target_language_code": target_language,
            },
        )
    except FileNotFoundError:
        return f"""請將每個區塊翻譯為 target_language。若提供 preferred_terms，必須優先使用。
 若提供 placeholder_tokens，必須完整保留，不可改動。
 若 payload 中含 context，必須遵守其規則。
 輸出需符合 contract_schema_example 的 JSON，且只輸出 JSON。

 目標語言：{_language_label(target_language)}
 目標語言代碼：{target_language}

 {_language_hint(target_language)}

 {payload}"""
