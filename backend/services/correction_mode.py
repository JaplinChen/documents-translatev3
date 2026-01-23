from __future__ import annotations

import re
from difflib import SequenceMatcher

from backend.services.language_detect import detect_language


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "").strip()


def _is_similar_text(a: str, b: str, threshold: float) -> bool:
    normalized_a = _normalize_text(a)
    normalized_b = _normalize_text(b)
    if not normalized_a or not normalized_b:
        return False
    if normalized_a == normalized_b:
        return False
    return SequenceMatcher(None, normalized_a, normalized_b).ratio() >= threshold


def prepare_blocks_for_correction(blocks: list[dict], target_language: str | None) -> list[dict]:
    if not target_language or target_language == "auto":
        return blocks
    prepared = []
    for block in blocks:
        text = block.get("source_text", "")
        if not text:
            prepared.append(block)
            continue
        detected = detect_language(text)
        if detected == target_language:
            prepared_block = dict(block)
            prepared_block["source_text"] = ""
            prepared.append(prepared_block)
            continue
        prepared.append(block)
    return prepared


def apply_correction_mode(
    blocks: list[dict],
    translated_texts: list[str],
    target_language: str | None,
    similarity_threshold: float = 0.75,
) -> list[dict]:
    output_blocks: list[dict] = []
    for idx, block in enumerate(blocks):
        translated_text = translated_texts[idx] if idx < len(translated_texts) else ""
        output_blocks.append(
            {
                "slide_index": block.get("slide_index"),
                "shape_id": block.get("shape_id"),
                "block_type": block.get("block_type"),
                "source_text": block.get("source_text", ""),
                "translated_text": translated_text,
                "client_id": block.get("client_id"),
                "correction_temp": False,
                "temp_translated_text": "",
            }
        )

    if not target_language or target_language == "auto":
        return output_blocks

    pending: list[dict] = []

    for idx, block in enumerate(output_blocks):
        source_text = block.get("source_text", "")
        detected = detect_language(source_text) if source_text else None

        if detected == target_language:
            match_index = None
            match_score = 0.0
            for pending_index, pending_item in enumerate(pending):
                if not _is_similar_text(source_text, pending_item["translated_text"], similarity_threshold):
                    continue
                score = SequenceMatcher(
                    None,
                    _normalize_text(source_text),
                    pending_item["normalized_text"],
                ).ratio()
                if score > match_score:
                    match_score = score
                    match_index = pending_index

            if match_index is not None:
                matched = pending.pop(match_index)
                block["translated_text"] = matched["translated_text"]
                source_block = output_blocks[matched["source_index"]]
                source_block["correction_temp"] = False
                source_block["temp_translated_text"] = ""
            else:
                block["translated_text"] = ""
            continue

        block["temp_translated_text"] = block.get("translated_text", "")
        block["translated_text"] = ""
        block["correction_temp"] = True
        pending.append(
            {
                "source_index": idx,
                "translated_text": block["temp_translated_text"],
                "normalized_text": _normalize_text(block["temp_translated_text"]),
            }
        )

    return output_blocks
