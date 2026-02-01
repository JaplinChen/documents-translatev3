from __future__ import annotations

import json
import logging
import os

from backend.services.llm_clients import (
    GeminiTranslator,
    MockTranslator,
    OllamaTranslator,
    OpenAITranslator,
    TranslationConfig,
)
from backend.services.translate_config import (
    get_language_hint,
    get_language_label,
)

from backend.services.learning_service import detect_domain, get_learned_terms

LOGGER = logging.getLogger(__name__)

# 常見 IT 品牌與術語修正建議 (智慧糾錯)
COMMON_TYPO_MAP = {
    "lapop": "Laptop",
    "bluetouch": "Bluetooth",
    "mitsum": "Mitsumi",
    "fuhlen": "Fuhlen",
    "rapoo": "Rapoo",
}

# 提取時注入的品牌提示，協助 LLM 識別
IT_BRAND_HINTS = [
    "Mitsumi (美津米/美律)",
    "Fuhlen (富勒)",
    "Rapoo (雷柏)",
    "Newmen (新曼)",
    "Genius (昆盈/精靈)",
    "Logitech (羅技)",
    "Asus (華碩)",
    "Acer (宏碁)",
    "Dell (戴爾)",
    "HP (惠普)",
    "Lenovo (聯想)",
]


def _suggest_typo_corrections(text: str) -> str:
    """針對文本進行初步的錯字建議註記，不直接修改原文，但提供提示。"""
    hints = []
    text_lower = text.lower()
    for typo, correction in COMMON_TYPO_MAP.items():
        if typo in text_lower:
            hints.append(f"注意：原文中的 '{typo}' 可能應為 '{correction}'。")
    return "\n".join(hints) if hints else ""


def _load_existing_terms(target_lang: str) -> list[str]:
    """
    Load existing terms from term repository and glossary to avoid duplicates.
    Returns a list of source text terms (lowercase) that already exist.
    """
    existing = set()

    # Load from unified term repository
    try:
        from backend.services.term_repository import list_terms

        terms = list_terms({"status": "active"})
        for t in terms:
            term_text = t.get("term", "").strip().lower()
            if term_text:
                existing.add(term_text)
    except Exception as e:
        LOGGER.warning(f"Failed to load terms from repository: {e}")

    # Load from glossary
    try:
        from backend.services.translation_memory import get_glossary

        glossary = get_glossary(limit=1000)
        for g in glossary:
            source_text = g.get("source_text", "").strip().lower()
            if source_text:
                existing.add(source_text)
    except Exception as e:
        LOGGER.warning(f"Failed to load glossary entries: {e}")

    return list(existing)


def _parse_json_array(content: str) -> list:
    """
    Parse JSON array from LLM response.
    Handles both raw JSON and markdown-wrapped JSON.
    """
    if not content or not content.strip():
        return []

    text = content.strip()

    # Try direct parse first
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
        return []
    except json.JSONDecodeError:
        pass

    # Try to find JSON array pattern [...]
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            result = json.loads(text[start : end + 1])
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    return []


def _validate_and_filter_terms(terms: list, existing_terms: set) -> list:
    """
    Validate term structure and filter out problematic terms.
    """
    import re

    valid_categories = {"product", "brand", "person", "place", "technical", "abbreviation", "other"}

    # Expanded generic words list
    GENERIC_WORDS = {
        "no.",
        "no",
        "none",
        "total",
        "sum",
        "status",
        "date",
        "summary",
        "table",
        "page",
        "index",
        "note",
        "name",
        "type",
        "size",
        "price",
        "quantity",
        "amount",
        "description",
        "item",
        "unit",
        "value",
        "count",
        "number",
        "month",
        "year",
        "day",
        "week",
        "time",
        "file",
        "folder",
        "document",
        "report",
        "list",
        "data",
        "info",
        "detail",
        "other",
        "all",
        "yes",
        "ok",
        "cancel",
        "save",
        "delete",
        "edit",
        "add",
        "remove",
        "update",
        "new",
        "old",
        "copy",
        "paste",
        "cut",
        "undo",
        "redo",
        "open",
        "close",
        "start",
        "end",
        "begin",
        "finish",
        "next",
        "previous",
        "first",
        "last",
        "top",
        "bottom",
        "left",
        "right",
        "up",
        "down",
        "in",
        "out",
        "on",
        "off",
        "true",
        "false",
        "enable",
        "disable",
        "active",
        "inactive",
        "valid",
        "invalid",
        "success",
        "error",
        "warning",
        "failed",
        "pending",
        "complete",
        "draft",
        "final",
        "version",
        "revision",
        "ram",
        "ram (gb)",
        "cpu",
        "gpu",
        "ssd",
        "hdd",
        "monitor",
        "projector",
        "keyboard",
        "mouse",
        "cable",
        "adapter",
        "battery",
        "serial number",
        "part number",
        "asset tag",
        "mac address",
        "ip address",
        "warranty",
        "model name",
        "purchase date",
        "no.",
        "授權",
        "彙總",
        "購買",
        "軟體",
        "硬體",
        "套數",
        "套件",
        "費用",
        "製作",
        "週期",
        "流程",
        "系統",
        "效果",
        "成本",
        "門檻",
        "品質",
        "內容",
        "資料",
    }

    # Negative patterns for descriptive phrases
    DESCRIPTIVE_KEYWORDS = {
        "的",
        "不",
        "非",
        "無",
        "未",
        "參差",
        "不齊",
        "優質",
        "惡劣",
        "昂貴",
        "廉價",
        "建議",
        "功能",
    }

    # Pattern for pure version numbers (without brand)
    VERSION_PATTERN = re.compile(r"^\d+\s*(pro|plus|max|ultra|lite|oem)?$", re.IGNORECASE)

    # Pattern for spec descriptions
    SPEC_PATTERN = re.compile(r"\d+\s*(gb|tb|ghz|mhz|mb|inch|mm|cm|pcs|kg|m|%)\b", re.IGNORECASE)

    # Aggressive patterns for hardware/software models
    MODEL_PATTERNS = [
        re.compile(
            r"^(Core|Ryzen|Xeon|RTX|GTX|Geforce|Quadro|Ultra|Optiplex|MacBook|iPad|iPhone|Galaxy)\s+.*",
            re.IGNORECASE,
        ),
        re.compile(r"^[0-9A-F]{2}(:[0-9A-F]{2}){5}$", re.IGNORECASE),  # MAC
        re.compile(r"^.*[0-9]+\.[0-9]+.*$"),  # Version like 1.2.3
    ]

    filtered = []
    seen_sources = set()

    for t in terms:
        if not isinstance(t, dict):
            continue

        source = t.get("source", "").strip()
        if not source:
            continue

        source_lower = source.lower()

        # === NEW FILTERS ===

        # 1. Skip combination terms (contains + or & and not a brand)
        if (" + " in source or " & " in source) and len(source.split()) > 2:
            LOGGER.debug(f"Skipping combination term: {source}")
            continue

        # 2. Skip pure version numbers
        if VERSION_PATTERN.match(source):
            LOGGER.debug(f"Skipping pure version number: {source}")
            continue

        # 3. Skip spec descriptions
        if SPEC_PATTERN.search(source) and len(source.split()) <= 3:
            LOGGER.debug(f"Skipping spec description: {source}")
            continue

        # 4. Skip generic words
        if source_lower in GENERIC_WORDS or any(
            w in source_lower for w in ["授權", "彙總", "套數", "序號"]
        ):
            LOGGER.debug(f"Skipping generic word or phrase: {source}")
            continue

        # 5. Skip if too short (single character or 2-letter non-abbreviation)
        if len(source) <= 2 and not source.isupper():
            LOGGER.debug(f"Skipping too short term: {source}")
            continue

        # 6. Aggressive model/noise patterns
        if any(p.match(source) for p in MODEL_PATTERNS):
            LOGGER.debug(f"Skipping model/noise pattern: {source}")
            continue

        # == NEW FILTERS V2.1 (Precision Optimization) ==

        # 7. Skip if contains descriptive keywords (like "的", "不", "參差")
        if any(kw in source for kw in DESCRIPTIVE_KEYWORDS):
            LOGGER.debug(f"Skipping descriptive/phrase term: {source}")
            continue

        # 8. Skip if ends with sentence punctuation (likely a sentence, not a term)
        if source.strip().endswith((".", "!", "?", "。", "！", "？", "：", ":")):
            LOGGER.debug(f"Skipping sentence-like term: {source}")
            continue

        # 8. Identity Filter: Skip if source == target (case-insensitive)
        # and contains only western characters (likely an IT model/code)
        target = t.get("target", "").strip()
        if source.lower() == target.lower():
            # If it's purely English/numbers/symbols, it doesn't need to be a glossary term
            if not re.search(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]", source):
                LOGGER.debug(f"Skipping identical source/target technical term: {source}")
                continue

        # 9. Length constraints (收緊限制)
        if len(source.split()) > 3:  # Too many words (reduced from 4)
            LOGGER.debug(f"Skipping too many words: {source}")
            continue
        if len(source) > 12 and re.search(
            r"[\u4e00-\u9fa5]", source
        ):  # Too long Chinese (reduced from 15)
            LOGGER.debug(f"Skipping long Chinese description: {source}")
            continue
        if any(c.isdigit() for c in source) and any(c.isalpha() for c in source):
            # If it's a single word with both numbers and letters (like SFG16-72)
            if len(source.split()) == 1 and len(source) > 6:
                LOGGER.debug(f"Skipping alphanumeric model: {source}")
                continue

        # === EXISTING FILTERS ===

        # Skip if already exists
        if source_lower in existing_terms:
            LOGGER.debug(f"Skipping existing term: {source}")
            continue

        # Skip duplicates in this batch
        if source_lower in seen_sources:
            continue
        seen_sources.add(source_lower)

        # Validate and normalize fields
        category = t.get("category", "other")
        if category not in valid_categories:
            category = "other"

        confidence = t.get("confidence", 5)
        try:
            confidence = int(confidence)
            confidence = max(1, min(10, confidence))  # Clamp to 1-10
        except (ValueError, TypeError):
            confidence = 5

        # Only keep terms with confidence >= 5
        if confidence < 5:
            LOGGER.debug(f"Skipping low confidence term: {source} ({confidence})")
            continue

        filtered.append(
            {
                "source": source,
                "target": t.get("target", ""),
                "category": category,
                "confidence": confidence,
                "reason": t.get("reason", ""),
            }
        )

    # Sort by confidence descending
    filtered.sort(key=lambda x: x.get("confidence", 0), reverse=True)

    return filtered


def extract_glossary_terms(  # noqa: C901
    blocks: list[dict],
    target_language: str,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> dict:
    """
    Extract key terminology from document blocks using LLM.
    Returns: {"terms": [...], "domain": "..."}
    """
    mode = os.getenv("TRANSLATE_LLM_MODE", "real").lower()

    if mode == "mock":
        client = MockTranslator()
    else:
        resolved_provider = (provider or "openai").lower()
        if resolved_provider in {"openai", "chatgpt", "gpt-4o"}:
            config = TranslationConfig(
                model=model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                api_key=api_key or os.getenv("OPENAI_API_KEY", ""),
                base_url=base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            )
            client = OpenAITranslator(config)
        elif resolved_provider == "gemini":
            client = GeminiTranslator(
                api_key=api_key or os.getenv("GEMINI_API_KEY", ""),
                base_url=base_url
                or os.getenv(
                    "GEMINI_BASE_URL",
                    "https://generativelanguage.googleapis.com/v1beta",
                ),
                model=model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            )
        elif resolved_provider == "ollama":
            client = OllamaTranslator(
                model=model or os.getenv("OLLAMA_MODEL", "llama3.1"),
                base_url=base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            )
        else:
            client = MockTranslator()

    # Consolidate all text for extraction
    # Support both 'original_text' (frontend) and 'source_text' (legacy).
    full_text = "\n".join(
        [
            b.get("original_text") or b.get("source_text", "")
            for b in blocks
            if b.get("original_text") or b.get("source_text")
        ]
    )
    if not full_text.strip():
        LOGGER.warning("No text content found in blocks for glossary extraction")
        return []

    # Limit text size to avoid token limit
    text_sample = full_text[:10000]

    # Load existing terms to exclude
    existing_terms = _load_existing_terms(target_language)
    existing_terms_set = set(t.lower() for t in existing_terms)

    # Format existing terms for prompt (limit to 100 to avoid overwhelming)
    if existing_terms:
        existing_display = existing_terms[:100]
        existing_terms_str = ", ".join(existing_display)
        if len(existing_terms) > 100:
            existing_terms_str += f" ... (還有 {len(existing_terms) - 100} 個)"
    else:
        existing_terms_str = "(無)"

    from backend.services.prompt_store import render_prompt

    # 產生智慧糾錯與品牌提示
    typo_hints = _suggest_typo_corrections(text_sample)
    brand_context = ", ".join(IT_BRAND_HINTS)

    # === 自動學習：歷史挖掘與領域偵測 ===
    domain = detect_domain(text_sample)
    learned = get_learned_terms(target_language, min_count=2, limit=20)
    learned_str = ""
    if learned:
        learned_str = "\n".join([f"- {item['source']} -> {item['target']}" for item in learned])
    else:
        learned_str = "(尚無使用者習慣紀錄)"

    prompt = render_prompt(
        "glossary_extraction",
        {
            "target_language": get_language_label(target_language),
            "text_sample": text_sample,
            "language_hint": get_language_hint(target_language),
            "existing_terms": existing_terms_str,
            "typo_hints": typo_hints or "(無)",
            "brand_hints": brand_context,
            "domain_context": domain,
            "learned_context": learned_str,
        },
    )

    try:
        if hasattr(client, "complete"):
            response = client.complete(prompt)
        elif hasattr(client, "translate_plain"):
            response = client.translate_plain(prompt)
        else:
            return []

        # Parse JSON array from response
        raw_terms = _parse_json_array(response)

        # Validate and filter terms
        terms = _validate_and_filter_terms(raw_terms, existing_terms_set)
        return {"terms": terms, "domain": domain}

    except ConnectionError as e:
        # Connection errors should be raised to inform the user
        LOGGER.error(f"Connection error extracting glossary: {e}")
        raise RuntimeError(str(e)) from e
    except Exception as e:
        error_msg = str(e)
        LOGGER.error(f"Error extracting glossary: {error_msg}")
        # If it's a connection-related error, raise it
        if (
            "連線" in error_msg
            or "connect" in error_msg.lower()
            or "connection" in error_msg.lower()
        ):
            raise RuntimeError(error_msg) from e
        # For other errors (like JSON parsing), return empty list
        return []
