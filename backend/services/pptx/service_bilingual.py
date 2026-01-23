from __future__ import annotations
from pptx import Presentation
from pptx.dml.color import RGBColor
from .apply_core import _apply_translations_to_presentation
from .apply_layout import duplicate_slide, insert_slide_after, iter_table_cells, find_shape_with_id, find_shape_in_shapes, add_overflow_textboxes, capture_font_spec
from .xml_core import get_pptx_theme_summary
from backend.services.font_manager import estimate_scale
from .text_utils import parse_hex_color, split_text_chunks
from .apply_text import set_bilingual_text, set_text_preserve_format

def apply_bilingual(
    pptx_in: str,
    pptx_out: str,
    blocks: list[dict],
    layout: str = "inline",
    target_language: str | None = None,
    font_mapping: dict[str, list[str]] | None = None,
) -> None:
    presentation = Presentation(pptx_in)
    presentation._pptx_path = pptx_in 
    table_cell_positions = {}
    table_cell_index = {}
    supported_types = {"textbox", "table_cell", "notes"}

    if layout == "new_slide":
        slide_blocks: dict[int, list[dict]] = {}
        for block in blocks:
            if block.get("apply") is False or block.get("selected") is False:
                continue
            slide_index = block.get("slide_index")
            if slide_index is None:
                continue
            slide_blocks.setdefault(slide_index, []).append(block)

        new_blocks = []
        offset = 0
        for slide_index in range(len(presentation.slides)):
            if slide_index not in slide_blocks:
                continue
            source_slide = presentation.slides[slide_index + offset]
            try:
                res = duplicate_slide(presentation, source_slide)
                new_slide, shape_map = res if isinstance(res, tuple) else (res, {})
            except Exception:
                new_slide = presentation.slides.add_slide(presentation.slide_layouts[6])
                shape_map = {}

            insert_slide_after(presentation, new_slide, slide_index + offset)
            offset += 1
            new_slide_index = slide_index + offset

            for block in slide_blocks[slide_index]:
                updated = dict(block)
                updated["slide_index"] = new_slide_index
                updated["layout"] = layout
                old_sid = updated.get("shape_id")
                if old_sid in shape_map:
                    updated["shape_id"] = shape_map[old_sid]
                new_blocks.append(updated)

        _apply_translations_to_presentation(presentation, new_blocks, mode="direct", target_language=target_language, font_mapping=font_mapping)
        presentation.save(pptx_out)
        return

    theme_data = get_pptx_theme_summary(pptx_in)
    translated_color = RGBColor(0x1F, 0x77, 0xB4)
    if theme_data and "colors" in theme_data and "accent1" in theme_data["colors"]:
        try:
            translated_color = parse_hex_color(theme_data["colors"]["accent1"])
        except Exception: pass

    for block in blocks:
        if block.get("apply") is False or block.get("selected") is False: continue
        if block.get("block_type") not in supported_types: continue
        translated_text = block.get("translated_text", "")
        if not translated_text: continue
        slide_index, shape_id = block.get("slide_index"), block.get("shape_id")
        if slide_index is None or shape_id is None or slide_index >= len(presentation.slides): continue
        
        slide = presentation.slides[slide_index]
        source_text = block.get("source_text", "")
        target_lang = block.get("target_language") or target_language
        combined_text = f"{source_text}\n\n{translated_text}"
        scale = estimate_scale(source_text, translated_text)

        if block.get("block_type") == "notes":
            if not slide.has_notes_slide: continue
            notes_shape = find_shape_in_shapes(slide.notes_slide.shapes, shape_id)
            if notes_shape and notes_shape.has_text_frame:
                if not set_bilingual_text(notes_shape.text_frame, source_text, translated_text, auto_size=layout == "auto", scale=scale, theme_data=theme_data, target_language=target_lang, font_mapping=font_mapping):
                    set_text_preserve_format(notes_shape.text_frame, combined_text, scale=scale)
            continue

        shape = find_shape_with_id(slide, shape_id)
        if not shape: continue

        if block.get("block_type") == "table_cell" and shape.has_table:
            key = (slide_index, shape_id)
            if key not in table_cell_positions:
                table_cell_positions[key] = iter_table_cells(shape)
                table_cell_index[key] = 0
            idx = table_cell_index[key]
            cells = table_cell_positions[key]
            if idx < len(cells):
                if not set_bilingual_text(cells[idx], source_text, translated_text, auto_size=layout == "auto", scale=scale, theme_data=theme_data, target_language=target_lang, font_mapping=font_mapping):
                    set_text_preserve_format(cells[idx], combined_text, scale=scale)
                table_cell_index[key] = idx + 1
            continue

        if not shape.has_text_frame: continue
        if layout == "auto" and len(translated_text) > 400:
            set_text_preserve_format(shape.text_frame, source_text)
            chunks = split_text_chunks(translated_text, 300)
            add_overflow_textboxes(slide, shape, chunks, capture_font_spec(shape.text_frame), translated_color, presentation.slide_height)
        elif not set_bilingual_text(shape.text_frame, source_text, translated_text, auto_size=layout == "auto", scale=scale, theme_data=theme_data, target_language=target_lang, font_mapping=font_mapping):
            set_text_preserve_format(shape.text_frame, combined_text, scale=scale)

    presentation.save(pptx_out)
