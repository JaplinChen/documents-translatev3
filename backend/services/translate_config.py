"""Translation configuration constants and helper functions.

This module contains language-related constants, provider defaults,
and utility functions for translation configuration.
"""

from __future__ import annotations

# Language code to label mapping
LANGUAGE_LABELS = {
    "zh-TW": "Traditional Chinese (zh-TW)",
    "zh-CN": "Simplified Chinese (zh-CN)",
    "zh": "Chinese (zh)",
    "vi": "Vietnamese (vi)",
    "en": "English (en)",
    "ja": "Japanese (ja)",
    "ko": "Korean (ko)",
}

# Language-specific hints for LLM
LANGUAGE_HINTS = {
    "vi": (
        "【重要】請務必使用「越南語」(Tiếng Việt) 進行翻譯。\n"
        "1. 語氣：請使用專業正式的商務語氣。\n"
        "2. 字符：必須正確使用越南語聲調與字母 (ă, â, ê, ô, ơ, ư, đ)。\n"
        "3. 技術名詞：常見技術名詞（如 AI, API, Cloud）可保留英文縮寫，\n"
        "   但可在括號內提供越南語說明。\n"
        "4. 範例：解決方案 → Giải pháp, 自動 → Tự động。\n"
        "嚴禁混雜菲律賓語、泰語、西班牙語或英文內容。\n"
        "錯誤示例：Solusyon（菲律賓語）"
    ),
    "zh-TW": (
        "請使用「繁體中文（台灣）」。\n"
        "1. 標點符號：必須使用全形標點（，。：；！？），引號請使用「」。\n"
        "2. 技術用語：務必符合台灣習慣。例如：使用「伺服器」而非"
        "「服務器」、「記憶體」而非「內存」、「使用者」而非「用戶」、"
        "「專案」而非「項目」、「貼上」而非「粘貼」。\n"
        "3. 語法：避免使用冗餘的「進行」、「的一個」等西化或大陸式語句，保持自然流暢。"
    ),
    "zh-CN": (
        "請使用「簡體中文（中國大陸）」。用語需符合當地的技術用語習慣"
        "（例如：使用「內存」而非「記憶體」）。"
    ),
    "zh": "請使用中文翻譯。",
    "en": "Please respond in professional English.",
    "ja": "日本語（熟語やビジネス表現）で回答してください。",
    "ko": "한국어(비즈니스 수준)로 답해주세요。",
}

# Few-shot examples to force correct language output
LANGUAGE_EXAMPLES = {
    "vi": ("<<<BLOCK:0>>>\nGiải pháp doanh nghiệp chuyên nghiệp\n<<<END>>>"),
    "zh-TW": ("<<<BLOCK:0>>>\n專業的企業級解決方案\n<<<END>>>"),
    "zh-CN": ("<<<BLOCK:0>>>\n专业的企业级解决方案\n<<<END>>>"),
    "en": ("<<<BLOCK:0>>>\nProfessional Enterprise Solutions\n<<<END>>>"),
    "ja": ("<<<BLOCK:0>>>\nプロフェッショナルな企業向けソリューション\n<<<END>>>"),
    "ko": ("<<<BLOCK:0>>>\n전문 기업용 솔루션\n<<<END>>>"),
}

# Provider-specific default configurations
PROVIDER_DEFAULTS = {
    "ollama": {
        "chunk_size": 6,
        "max_retries": 1,
        "chunk_delay": 0.0,
        "single_request": False,
    },
    "gemini": {
        "chunk_size": 4,
        "max_retries": 2,
        "chunk_delay": 1.0,
        "single_request": True,
    },
    "openai": {
        "chunk_size": 40,
        "max_retries": 2,
        "chunk_delay": 0.0,
        "single_request": True,
    },
}


def get_language_label(code: str) -> str:
    """Get human-readable label for a language code."""
    normalized = (code or "").strip()
    return LANGUAGE_LABELS.get(normalized, normalized or code)


def get_language_hint(code: str) -> str:
    """Get language-specific hint for LLM prompts."""
    normalized = (code or "").strip()
    return LANGUAGE_HINTS.get(normalized, "")


def get_language_example(code: str) -> str:
    """Get few-shot example for a language code."""
    normalized = (code or "").strip()
    return LANGUAGE_EXAMPLES.get(normalized, "")


def get_tone_instruction(tone: str | None) -> str:
    """Get tone-specific instruction for translation."""
    if not tone or tone == "professional":
        return "請使用專業商務語氣，用語得體、準確。"
    tones = {
        "concise": "請保持語句極致簡潔，去除冗餘修飾，適合簡報展示。",
        "humorous": "請使用風趣幽默、活潑的語氣，增加親和力與趣味性。",
        "creative": "請富有創意，運用修辭與動感詞彙，吸引觀眾注意。",
        "pm": "請以產品經理 (PM) 視角進行翻譯，強調商業價值、邏輯性與執行力。",
        "academic": "請使用學術及嚴謹的語氣，用語精確並符合術語標準。",
    }
    return tones.get(tone, "")


def get_vision_context_instruction(use_vision: bool) -> str:
    """Get vision context instruction for translation."""
    if not use_vision:
        return ""
    return (
        "請根據簡報的視覺情境進行翻譯。標題(Title)應簡短醒目，"
        "內文(Content)應邏輯分明，備註(Notes)應詳細完整。"
    )


def get_provider_config(
    provider: str,
    key: str,
    default: int | float | bool,
) -> int | float | bool:
    """Get provider-specific configuration value."""
    provider_defaults = PROVIDER_DEFAULTS.get(provider, {})
    return provider_defaults.get(key, default)
