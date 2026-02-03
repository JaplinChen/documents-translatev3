from __future__ import annotations

import logging
import re

LOGGER = logging.getLogger(__name__)


def _validate_and_filter_terms(terms: list, existing_terms: set) -> list:
    """
    Validate term structure and filter out problematic terms.
    """
    valid_categories = {"product", "brand", "person", "place", "technical", "abbreviation", "other"}

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

    VERSION_PATTERN = re.compile(r"^\d+\s*(pro|plus|max|ultra|lite|oem)?$", re.IGNORECASE)
    SPEC_PATTERN = re.compile(r"\d+\s*(gb|tb|ghz|mhz|mb|inch|mm|cm|pcs|kg|m|%)\b", re.IGNORECASE)
    MODEL_PATTERNS = [
        re.compile(
            r"^(Core|Ryzen|Xeon|RTX|GTX|Geforce|Quadro|Ultra|Optiplex|MacBook|iPad|iPhone|Galaxy)\s+.*",
            re.IGNORECASE,
        ),
        re.compile(r"^[0-9A-F]{2}(:[0-9A-F]{2}){5}$", re.IGNORECASE),
        re.compile(r"^.*[0-9]+\.[0-9]+.*$"),
    ]

    filtered = []
    seen_sources = set()

    for term in terms:
        if not isinstance(term, dict):
            continue

        source = term.get("source", "").strip()
        if not source:
            continue

        source_lower = source.lower()

        if (" + " in source or " & " in source) and len(source.split()) > 2:
            LOGGER.debug(f"Skipping combination term: {source}")
            continue

        if VERSION_PATTERN.match(source):
            LOGGER.debug(f"Skipping pure version number: {source}")
            continue

        if SPEC_PATTERN.search(source) and len(source.split()) <= 3:
            LOGGER.debug(f"Skipping spec description: {source}")
            continue

        if source_lower in GENERIC_WORDS or any(
            word in source_lower for word in ["授權", "彙總", "套數", "序號"]
        ):
            LOGGER.debug(f"Skipping generic word or phrase: {source}")
            continue

        if len(source) <= 2 and not source.isupper():
            LOGGER.debug(f"Skipping too short term: {source}")
            continue

        if any(pattern.match(source) for pattern in MODEL_PATTERNS):
            LOGGER.debug(f"Skipping model/noise pattern: {source}")
            continue

        if any(keyword in source for keyword in DESCRIPTIVE_KEYWORDS):
            LOGGER.debug(f"Skipping descriptive/phrase term: {source}")
            continue

        if source.strip().endswith((".", "!", "?", "。", "！", "？", "：", ":")):
            LOGGER.debug(f"Skipping sentence-like term: {source}")
            continue

        target = term.get("target", "").strip()
        if source.lower() == target.lower():
            if not re.search(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]", source):
                LOGGER.debug(f"Skipping identical source/target technical term: {source}")
                continue

        if len(source.split()) > 3:
            LOGGER.debug(f"Skipping too many words: {source}")
            continue
        if len(source) > 12 and re.search(r"[\u4e00-\u9fa5]", source):
            LOGGER.debug(f"Skipping long Chinese description: {source}")
            continue
        if any(c.isdigit() for c in source) and any(c.isalpha() for c in source):
            if len(source.split()) == 1 and len(source) > 6:
                LOGGER.debug(f"Skipping alphanumeric model: {source}")
                continue

        if source_lower in existing_terms:
            LOGGER.debug(f"Skipping existing term: {source}")
            continue

        if source_lower in seen_sources:
            continue
        seen_sources.add(source_lower)

        category = term.get("category", "other")
        if category not in valid_categories:
            category = "other"

        confidence = term.get("confidence", 5)
        try:
            confidence = int(confidence)
            confidence = max(1, min(10, confidence))
        except (ValueError, TypeError):
            confidence = 5

        if confidence < 5:
            LOGGER.debug(f"Skipping low confidence term: {source} ({confidence})")
            continue

        filtered.append(
            {
                "source": source,
                "target": term.get("target", ""),
                "category": category,
                "confidence": confidence,
                "reason": term.get("reason", ""),
            }
        )

    filtered.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    return filtered
