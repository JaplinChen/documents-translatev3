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


def _filter_effective_blocks(blocks_data: list[dict], completed_ids: set, refresh: bool) -> tuple[list[dict], int]:
    effective_blocks = []
    skipped_count = 0
    for block in blocks_data:
        text = block.get("source_text", "")
        has_vi = bool(VI_REGEX.search(text))

        if refresh and has_vi:
            effective_blocks.append(block)
            continue

        if not refresh and block.get("client_id") in completed_ids:
            skipped_count += 1
            continue
        effective_blocks.append(block)
    return effective_blocks, skipped_count
