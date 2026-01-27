from __future__ import annotations

import fitz  # PyMuPDF

def apply_translations(
    input_path: str,
    output_path: str,
    blocks: list[dict],
):
    """Apply translations by overlaying translated text."""
    doc = fitz.open(input_path)
    page_map = {}
    for block in blocks:
        p_idx = block.get("slide_index", 0)
        if p_idx not in page_map:
            page_map[p_idx] = []
        page_map[p_idx].append(block)

    for p_idx, page_blocks in page_map.items():
        if p_idx >= len(doc):
            continue
        page = doc[p_idx]
        for block in page_blocks:
            translated_text = block.get("translated_text", "").strip()
            if not translated_text:
                continue
            x0 = block.get("x")
            y0 = block.get("y")
            w = block.get("width")
            h = block.get("height")
            font_size = block.get("font_size", 10.0)
            font_name = block.get("font_name", "helv")
            if None in (x0, y0, w, h):
                continue
            rect = fitz.Rect(x0, y0, x0 + w, y0 + h)
            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
            try:
                page.insert_textbox(
                    rect,
                    translated_text,
                    fontsize=font_size,
                    fontname=font_name,
                    align=fitz.TEXT_ALIGN_LEFT,
                )
            except Exception:
                page.insert_textbox(
                    rect,
                    translated_text,
                    fontsize=font_size,
                    fontname="helv",
                )
    doc.save(output_path)
    doc.close()


def apply_bilingual(
    input_path: str,
    output_path: str,
    blocks: list[dict],
    layout: str = "inline",
):
    """Apply bilingual translations with dynamic font scaling."""
    doc = fitz.open(input_path)
    page_map = {}
    for block in blocks:
        p_idx = block.get("slide_index", 0)
        if p_idx not in page_map:
            page_map[p_idx] = []
        page_map[p_idx].append(block)
    for p_idx, page_blocks in page_map.items():
        if p_idx >= len(doc):
            continue
        page = doc[p_idx]
        for block in page_blocks:
            source_text = block.get("source_text", "").strip()
            translated_text = block.get("translated_text", "").strip()
            if not translated_text:
                continue
            bilingual_text = f"{source_text}\n{translated_text}"
            x0 = block.get("x")
            y0 = block.get("y")
            w = block.get("width")
            h = block.get("height")
            font_size = block.get("font_size", 10.0)
            font_name = block.get("font_name", "helv")
            if None in (x0, y0, w, h):
                continue
            scaled_font_size = max(font_size * 0.75, 6.0)
            rect = fitz.Rect(x0, y0, x0 + w, y0 + h)
            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
            try:
                page.insert_textbox(
                    rect,
                    bilingual_text,
                    fontsize=scaled_font_size,
                    fontname=font_name,
                    align=fitz.TEXT_ALIGN_LEFT,
                )
            except Exception:
                page.insert_textbox(
                    rect,
                    bilingual_text,
                    fontsize=scaled_font_size,
                    fontname="helv",
                )
    doc.save(output_path)
    doc.close()
