"""Ollama-specific prompt building and response parsing.

This module contains prompt construction logic for Ollama batch translation
and response parsing utilities.
"""

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


def build_ollama_batch_prompt(
    blocks: list[dict], target_language: str, strict: bool = False
) -> str:
    """Build batch translation prompt for Ollama.

    Args:
        blocks: List of text blocks to translate
        target_language: Target language code
        strict: If True, add stricter language verification

    Returns:
        Formatted prompt string for Ollama
    """
    label = get_language_label(target_language)
    hint = get_language_hint(target_language)
    example = get_language_example(target_language)
    language_guard = (
        f"【絕對指令】輸出的每一行、各區塊內容都「必須」使用目標語言 {label}。嚴禁出現原文、引導語或任何解釋標籤（如 [SOURCE_TEXT:]）。"
        if strict
        else f"輸出的每個區塊內容必須使用目標語言 {label}。請直接輸出翻譯後的文字，不要包含任何標籤。"
    )

    blocks_lines: list[str] = []
    for idx, block in enumerate(blocks):
        blocks_lines.append(f"<<<BLOCK:{idx}>>>")
        if block.get("alignment_source"):
            blocks_lines.append(f"[SOURCE_TEXT: {block.get('alignment_source')}]")
            blocks_lines.append(f"[EXISTING_TRANSLATION: {block.get('source_text')}]")
        else:
            blocks_lines.append(block.get("source_text", ""))
        blocks_lines.append("<<<END>>>")
        blocks_lines.append("")
    blocks_text = "\n".join(blocks_lines).strip()

    tone = os.getenv("LLM_TONE")
    use_vision = os.getenv("LLM_VISION_CONTEXT") == "1"
    tone_hint = get_tone_instruction(tone)
    vision_hint = get_vision_context_instruction(use_vision)

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
        parts = [
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
        return "\n".join(parts)


def parse_ollama_batch_response(text: str, count: int) -> list[str] | None:
    """Parse Ollama batch translation response.

    Args:
        text: Raw response text from Ollama
        count: Expected number of translated blocks

    Returns:
        List of translated texts if successful, None if format mismatch
    """
    pattern = re.compile(r"<<<BLOCK:(\d+)>>>\n(.*?)\n<<<END>>>", re.DOTALL)
    matches = pattern.findall(text)
    if not matches:
        return None

    translated = [""] * count
    # Regex to strip common leaked tags
    TAG_PATTERN = re.compile(r"\[(?:SOURCE_TEXT|EXISTING_TRANSLATION|ORIGINAL|TRANSLATED|Correction|Target):\s*.*?\]", re.IGNORECASE)

    for idx_str, content in matches:
        try:
            idx = int(idx_str)
        except ValueError:
            continue
        if 0 <= idx < count:
            # Clean content: remove leaked tags and trim
            cleaned = TAG_PATTERN.sub("", content).strip()
            # Remove repeated block markers if LLM nested them
            cleaned = re.sub(r"<<<BLOCK:\d+>>>|<<<END>>>", "", cleaned).strip()
            translated[idx] = cleaned

    if any(item == "" for item in translated):
        return None
    return translated
