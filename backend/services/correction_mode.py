from __future__ import annotations

import re
from difflib import SequenceMatcher

from backend.services.language_detect import detect_language

VI_DIACRITIC_PATTERN = (
    r"[đĐàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩị"
    r"òóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ]"
)


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "").strip()


def _is_similar_text(a: str, b: str, threshold: float) -> bool:
    normalized_a = _normalize_text(a)
    normalized_b = _normalize_text(b)
    if not normalized_a or not normalized_b:
        return False
    if normalized_a == normalized_b:
        return True
    return (
        SequenceMatcher(None, normalized_a, normalized_b).ratio()
        >= threshold
    )


def prepare_blocks_for_correction(
    blocks: list[dict],
    target_language: str | None,
) -> list[dict]:
    if not target_language or target_language == "auto":
        return blocks
    prepared = []
    for block in blocks:
        text = block.get("source_text", "")
        if not text:
            prepared.append(block)
            continue
        # Check if text contains source language characteristics.
        has_source_characteristics = bool(
            re.search(VI_DIACRITIC_PATTERN, text, re.I)
        )

        # [TRACE] Trace detection and decision
        # print(
        #     f"[CORRECTION_TRACE] Text: {text[:20]}... | "
        #     f"has_source: {has_source_characteristics}",
        #     flush=True,
        # )

        # If it's a bilingual block (has Vietnamese), we MUST keep
        # source_text for LLM to re-merge.
        if has_source_characteristics:
            prepared.append(block)
            continue
        detected = detect_language(text)
        if detected == target_language or detected == "zh-CN":
            # print(
            #     f"  [DECISION] CLEAR source_text for: {text[:20]}...",
            #     flush=True,
            # )
            prepared_block = dict(block)
            prepared_block["source_text"] = ""
            prepared.append(prepared_block)
            continue

        # print(
        #     f"  [DECISION] KEEP source_text for: {text[:20]}...",
        #     flush=True,
        # )
        prepared.append(block)
    return prepared


def apply_correction_mode(  # noqa: C901
    blocks: list[dict],
    translated_texts: list[str],
    target_language: str | None,
    similarity_threshold: float = 0.75,
) -> list[dict]:
    output_blocks: list[dict] = []
    for idx, block in enumerate(blocks):
        translated_text = (
            translated_texts[idx]
            if idx < len(translated_texts)
            else ""
        )
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

            # [IMPROVED] Search for matching block, accounting for
            # mixed language.
            for pending_index, pending_item in enumerate(pending):
                candidate_text = pending_item["translated_text"]

                # Check 1: Normal similarity
                if _is_similar_text(
                    source_text,
                    candidate_text,
                    similarity_threshold,
                ):
                    score = SequenceMatcher(
                        None,
                        _normalize_text(source_text),
                        pending_item["normalized_text"],
                    ).ratio()
                else:
                    # Check 2: If source_text has Vietnamese, it might be
                    # compared against pure Target text.
                    from backend.services.language_detect import (
                        _CJK_RE,
                        _VI_DIACRITIC_RE,
                    )
                    has_vi = bool(_VI_DIACRITIC_RE.search(source_text))
                    if has_vi:
                        # Only compare CJK parts
                        src_cjk = "".join(_CJK_RE.findall(source_text))
                        cand_cjk = "".join(_CJK_RE.findall(candidate_text))
                        if src_cjk and cand_cjk and _is_similar_text(
                            src_cjk,
                            cand_cjk,
                            similarity_threshold,
                        ):
                            score = SequenceMatcher(
                                None,
                                src_cjk,
                                cand_cjk,
                            ).ratio()
                        else:
                            continue
                    else:
                        continue

                if score > match_score:
                    match_score = score
                    match_index = pending_index

            if match_index is not None:
                matched = pending.pop(match_index)
                final_text = matched["translated_text"]

                # [STITCH_PATCH] Ensure Bilingual Consistency
                # If source text has Vietnamese but the matched translation
                # (LLM output) missing it, prepend it back.
                from backend.services.language_detect import _VI_DIACRITIC_RE
                src_vi_parts = _VI_DIACRITIC_RE.findall(source_text)
                if len(src_vi_parts) >= 2:  # Significant VI characteristic
                    if not _VI_DIACRITIC_RE.search(final_text):
                        # Extract the prefix VI part from source_text
                        # (usually before the CJK/Chinese begins).
                        # We use a simple but robust approach: find the
                        # first CJK index in source.
                        from backend.services.language_detect import _CJK_RE
                        cjk_match = _CJK_RE.search(source_text)
                        if cjk_match:
                            vi_prefix = source_text[:cjk_match.start()].strip()
                            if vi_prefix:
                                final_text = f"{vi_prefix} {final_text}"

                block["translated_text"] = final_text
                source_block = output_blocks[matched["source_index"]]
                source_block["correction_temp"] = False
                source_block["temp_translated_text"] = ""
            else:
                # If no match found, keep the existing translation or
                # LLM result.
                # Do not set to empty string.
                pass
            continue

        block["temp_translated_text"] = block.get("translated_text", "")
        block["translated_text"] = ""
        block["correction_temp"] = True
        pending.append(
            {
                "source_index": idx,
                "translated_text": block["temp_translated_text"],
                "normalized_text": _normalize_text(
                    block["temp_translated_text"]
                ),
            }
        )

    # Final Flush: If any items remain in pending, it means they were
    # not matched.
    # We should restore their translated_text so they don't appear empty.
    for matched in pending:
        source_idx = matched["source_index"]
        block = output_blocks[source_idx]
        if not block.get("translated_text"):
            block["translated_text"] = matched["translated_text"]
            block["correction_temp"] = False

    return output_blocks
