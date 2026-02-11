from __future__ import annotations

import json
import logging
import re

from fastapi import HTTPException

from backend.contracts import coerce_blocks
from backend.services.correction_mode import prepare_blocks_for_correction
from backend.services.language_detect import resolve_source_language

LOGGER = logging.getLogger(__name__)

VI_REGEX = re.compile(
    r"[đĐàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ]",
    re.I,
)


def _prepare_blocks_for_correction(
    items: list[dict],
    target_language: str | None,
) -> list[dict]:
    """Prepare blocks for correction mode.

    Skip blocks that match the target language.
    """
    return prepare_blocks_for_correction(items, target_language)


def _parse_blocks(blocks: str | list[dict], context: str) -> list[dict]:
    try:
        if isinstance(blocks, str):
            return coerce_blocks(json.loads(blocks))
        return coerce_blocks(blocks)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="blocks JSON 無效") from exc
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"blocks 資料無效 ({context})",
        ) from exc


def _resolve_language(blocks_data: list[dict], source_language: str | None) -> str | None:
    return resolve_source_language(
        blocks_data,
        source_language,
    )


def _resolve_param_overrides(
    provider: str | None, refresh: bool, ollama_fast_mode: bool
) -> dict:
    param_overrides = {"refresh": refresh}
    if (provider or "").lower() == "ollama" and ollama_fast_mode:
        param_overrides.update(
            {
                "single_request": False,
                "chunk_size": 1,
                "chunk_delay": 0.0,
            }
        )
    return param_overrides


def _resolve_completed_ids(completed_ids) -> set:
    completed_id_set = set()
    if completed_ids:
        try:
            if isinstance(completed_ids, str):
                completed_id_set = set(json.loads(completed_ids))
            elif isinstance(completed_ids, list):
                completed_id_set = set(completed_ids)
        except (json.JSONDecodeError, TypeError):
            pass
    return completed_id_set


def _filter_effective_blocks(
    blocks_data: list[dict], completed_ids: set, refresh: bool, layout_params: dict | None = None
) -> tuple[list[dict], int]:
    effective_blocks = []
    skipped_count = 0

    # Parse layout parameters
    params = layout_params or {}
    skip_numbers = params.get("skip_numbers", False)
    skip_dates = params.get("skip_dates", False)
    skip_code = params.get("skip_code", False)
    skip_translated = params.get("skip_translated", False)

    from backend.services.extract_utils import (
        is_numeric_only,
        is_garbage_text,
        is_technical_terms_only,
        is_symbol_only
    )

    DATE_RE = re.compile(r"^(\d{1,4}[-/.\s]){2,}\d{1,4}$")
    CJK_RE = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff]")  # Detected CJK
    LATIN_RE = re.compile(r"[a-zA-Zàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ]") # Broad Latin + VI

    for block in blocks_data:
        text = block.get("source_text", "")
        translated = block.get("translated_text", "")

        # Basic logic: skip already completed IDs if not refresh
        if not refresh and block.get("client_id") in completed_ids:
            skipped_count += 1
            continue

        # Skip already translated cells:
        # 1. 檢查翻譯結果欄位是否已有內容
        # 2. 偵測源文本是否已包含雙語混合內容（例如 Latin/越文 + 中文同時存在）
        if skip_translated:
            if translated and translated.strip():
                skipped_count += 1
                continue
            if CJK_RE.search(text) and LATIN_RE.search(text):
                skipped_count += 1
                continue

        # Skip simple symbols
        if is_symbol_only(text):
            skipped_count += 1
            continue

        # User-defined Excel skip parameters
        if skip_numbers and is_numeric_only(text):
            skipped_count += 1
            continue

        if skip_dates and DATE_RE.match(text.strip()):
            skipped_count += 1
            continue

        if skip_code and (is_garbage_text(text) or is_technical_terms_only(text)):
            skipped_count += 1
            continue

        effective_blocks.append(block)

    return effective_blocks, skipped_count
