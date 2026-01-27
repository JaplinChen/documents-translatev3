"""Ollama-specific prompt helpers."""

from __future__ import annotations

import os
import re

from backend.services.prompt_store import render_prompt
from backend.services.translate_config import (
    get_language_example,
    get_language_hint,
    get_language_label,
    get_tone_instruction,
    get_vision_context_instruction,
)

BLOCK_RESPONSE_PATTERN = re.compile(
    r"<<<BLOCK:(\d+)>>>\n(.*?)\n<<<END>>>", re.DOTALL
)
TAG_PATTERN = re.compile(
    r"\[(?:SOURCE_TEXT|EXISTING_TRANSLATION|ORIGINAL|TRANSLATED|"
    r"Correction|Target):\s*.*?\]",
    re.IGNORECASE,
)


def build_ollama_batch_prompt(
    blocks: list[dict],
    target_language: str,
    strict: bool = False,
) -> str:
    """Build Ollama batch prompt."""
    label = get_language_label(target_language)
    hint = get_language_hint(target_language)
    example = get_language_example(target_language)
    language_guard = (
        (
            f"【絕對指令】輸出的每一行、各區塊內容都「必須」使用目標語言 {label}。"
            " 嚴禁出現原文、引導語或任何解釋標籤（如 [SOURCE_TEXT:]）。"
        )
        if strict
        else (
            f"輸出的每個區塊內容必須使用目標語言 {label}。"
            "請直接輸出翻譯後的文字，不要包含任何標籤。"
        )
    )

    blocks_text = _render_blocks(blocks)
    tone_hint = get_tone_instruction(os.getenv("LLM_TONE"))
    vision_hint = get_vision_context_instruction(
        os.getenv("LLM_VISION_CONTEXT") == "1"
    )

    try:
        return render_prompt(
            "ollama_batch",
            {
                "target_language_label": label,
                "target_language_code": target_language,
                "language_guard": language_guard,
                "language_hint": f"{hint}\n{tone_hint}\n{vision_hint}".strip(),
                "language_example": example,
                "blocks": blocks_text,
            },
        )
    except FileNotFoundError:
        return "\n".join(
            [
                "請將每個區塊翻譯為目標語言。",
                f"目標語言：{label}",
                f"目標語言代碼：{target_language}",
                hint,
                language_guard,
                "請參考正確輸出風格：",
                example,
                "",
                "請保留標記並只輸出翻譯文字。格式：",
                "<<<BLOCK:0>>>",
                "<翻譯文字>",
                "<<<END>>>",
                "",
                "待翻譯輸入：",
                blocks_text,
            ]
        )


def parse_ollama_batch_response(text: str, count: int) -> list[str] | None:
    """Parse Ollama batch translation response."""
    matches = BLOCK_RESPONSE_PATTERN.findall(text)
    if not matches:
        return None

    translated = [""] * count
    for idx_str, content in matches:
        if not idx_str.isdigit():
            continue
        idx = int(idx_str)
        if 0 <= idx < count:
            cleaned = TAG_PATTERN.sub("", content).strip()
            cleaned = re.sub(r"<<<BLOCK:\d+>>>|<<<END>>>", "", cleaned).strip()
            translated[idx] = cleaned

    if any(item == "" for item in translated):
        return None
    return translated


def _render_blocks(blocks: list[dict]) -> str:
    lines: list[str] = []
    for idx, block in enumerate(blocks):
        lines.append(f"<<<BLOCK:{idx}>>>")
        if block.get("alignment_source"):
            lines.append(f"[SOURCE_TEXT: {block.get('alignment_source')}]")
            lines.append(f"[EXISTING_TRANSLATION: {block.get('source_text')}]")
        else:
            lines.append(block.get("source_text", ""))
        lines.append("<<<END>>>")
        lines.append("")
    return "\n".join(lines).strip()
