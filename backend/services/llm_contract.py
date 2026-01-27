from __future__ import annotations

from collections.abc import Iterable

def build_contract(
    blocks: Iterable[dict],
    target_language: str,
    translated_texts: Iterable[str] | None,
) -> dict:
    output_blocks = []
    translated_iter = (
        iter(translated_texts)
        if translated_texts is not None
        else None
    )
    for block in blocks:
        translated_text = (
            next(translated_iter)
            if translated_iter is not None
            else block.get("source_text", "")
        )
        output_blocks.append(
            {
                "slide_index": block.get("slide_index"),
                "shape_id": block.get("shape_id"),
                "block_type": block.get("block_type"),
                "source_text": block.get("source_text", ""),
                "translated_text": translated_text,
                "client_id": block.get("client_id"),
            }
        )
    return {
        "document_language": "auto",
        "target_language": target_language,
        "blocks": output_blocks,
    }


def validate_contract(result: dict) -> None:
    if "blocks" not in result:
        raise ValueError("Missing blocks in LLM response")
    for block in result["blocks"]:
        for key in (
            "slide_index",
            "shape_id",
            "block_type",
            "source_text",
            "translated_text",
        ):
            if key not in block:
                raise ValueError(f"Missing {key} in LLM response block")


def coerce_contract(  # noqa: C901
    result: dict,
    blocks: list[dict],
    target_language: str,
) -> dict:
    if isinstance(result, dict) and "blocks" in result:
        return result

    candidate_list = None
    if isinstance(result, list):
        candidate_list = result
    elif isinstance(result, dict):
        for key in ("translations", "data", "items", "results", "output"):
            value = result.get(key)
            if isinstance(value, list):
                candidate_list = value
                break

    if candidate_list is None:
        return {"blocks": []}

    if candidate_list and all(
        isinstance(item, str) for item in candidate_list
    ):
        return build_contract(blocks, target_language, candidate_list)

    if candidate_list and all(
        isinstance(item, dict) for item in candidate_list
    ):
        translated_texts = []
        for i, item in enumerate(candidate_list):
            # 優先嘗試從 LLM 響應獲取譯文，若無則嘗試原始文字
            text = (
                item.get("translated_text")
                or item.get("translation")
                or item.get("text")
            )
            if not text and i < len(blocks):
                text = blocks[i].get("source_text", "")
            translated_texts.append(text or "")
        return build_contract(blocks, target_language, translated_texts)

    # 如果以上都失敗且我們有原始塊，至少返回結構正確的合約（譯文為空）
    return build_contract(blocks, target_language, translated_texts=None)
