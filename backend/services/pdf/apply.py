from __future__ import annotations

import logging
import os
import fitz


def _get_unicode_font(page, target_lang: str | None) -> str:
    """Register and return a unicode-safe font name for the given page."""
    # Common paths for Noto fonts in Debian/Ubuntu
    # 越南文使用 NotoSans-Regular, 中文使用 NotoSansCJK-Regular
    is_cjk = target_lang and target_lang.lower().startswith(("zh", "ja", "ko"))

    font_paths = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
        if is_cjk
        else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]

    for path in font_paths:
        if os.path.exists(path):
            try:
                # Use a unique name per page to avoid conflicts
                # PyMuPDF will handle embedding
                fname = f"uni-{target_lang}"
                page.insert_font(fontname=fname, fontfile=path)
                return fname
            except Exception:
                continue

    return "helv"  # Fallback


def apply_pdf_changes(
    input_path: str,
    output_path: str,
    blocks: list[dict],
    target_lang: str = "zh-TW",
    mode: str = "translated",
    layout_params: dict | None = None,
) -> None:
    """Apply translated blocks to PDF."""
    doc = fitz.open(input_path)
    options = layout_params or {}
    show_source = bool(options.get("show_source", True))
    sep_style = str(options.get("separator_style", "linebreak"))
    source_first = bool(options.get("source_first", True))
    font_scale = float(options.get("font_scale", 1.0) or 1.0)
    font_scale = max(0.5, min(font_scale, 2.0))

    if sep_style == "blank_line":
        separator = "\n\n"
    elif sep_style == "slash":
        separator = " / "
    else:
        separator = "\n"

    # Group blocks by page
    pages_blocks = {}
    for block in blocks:
        p_idx = block.get("page", 0)
        if p_idx not in pages_blocks:
            pages_blocks[p_idx] = []
        pages_blocks[p_idx].append(block)

    for p_idx, p_blocks in pages_blocks.items():
        if p_idx >= len(doc):
            continue

        page = doc[p_idx]
        # Register font once per page
        font_name = _get_unicode_font(page, target_lang)

        for block in p_blocks:
            # Draw white rectangle to cover old text
            if "box_2d" in block and block["box_2d"]:
                x0, y0, w, h = (
                    block["box_2d"][0],
                    block["box_2d"][1],
                    block["box_2d"][2],
                    block["box_2d"][3],
                )
            else:
                x0 = block.get("x", 0)
                y0 = block.get("y", 0)
                w = block.get("width", 0)
                h = block.get("height", 0)

            # Draw white background
            rect = fitz.Rect(x0, y0, x0 + w, y0 + h)
            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))

            # Insert new text
            source_text = block.get("source_text") or block.get("text", "")
            translated_text = block.get("translated_text") or block.get("text", "")
            if mode == "bilingual" and show_source:
                text = (
                    f"{source_text}{separator}{translated_text}"
                    if source_first
                    else f"{translated_text}{separator}{source_text}"
                )
            else:
                text = translated_text
            if text:
                try:
                    page.insert_textbox(
                        rect,
                        text,
                        fontsize=(block.get("font_size", 10) or 10.0) * font_scale,
                        fontname=font_name,
                        color=(0, 0, 0),
                        align=fitz.TEXT_ALIGN_LEFT,
                    )
                except Exception as e:
                    logging.error(f"Error inserting text blocks: {e}")

    doc.save(output_path)
    doc.close()


def apply_bilingual(
    input_path: str,
    output_path: str,
    blocks: list[dict],
    target_language: str | None = "zh-TW",
    layout_params: dict | None = None,
) -> None:
    """Apply bilingual changes to PDF."""
    apply_pdf_changes(
        input_path,
        output_path,
        blocks,
        target_lang=target_language or "zh-TW",
        mode="bilingual",
        layout_params=layout_params,
    )


def apply_translations(
    input_path: str,
    output_path: str,
    blocks: list[dict],
    target_language: str | None = "zh-TW",
    layout_params: dict | None = None,
) -> None:
    """Apply translated changes to PDF."""
    apply_pdf_changes(
        input_path,
        output_path,
        blocks,
        target_lang=target_language or "zh-TW",
        mode="translated",
        layout_params=layout_params,
    )
