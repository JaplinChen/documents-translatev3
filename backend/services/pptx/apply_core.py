from __future__ import annotations
from collections.abc import Iterable
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_AUTO_SIZE

from .apply_layout import (
    add_overflow_textboxes,
    capture_font_spec,
    find_shape_in_shapes,
    find_shape_with_id,
    iter_table_cells,
    fix_title_overlap,
)

from backend.services.font_manager import estimate_scale
from .text_utils import split_text_chunks
from .apply_text import (
    set_bilingual_text,
    set_text_preserve_format,
)
from .xml_core import get_pptx_theme_summary

def _apply_translations_to_presentation(
    presentation,
    blocks: Iterable[dict],
    mode: str = "direct",
    target_language: str | None = None,
    font_mapping: dict[str, list[str]] | None = None,
) -> None:
    table_cell_positions = {}
    table_cell_index = {}
    supported_types = {"textbox", "table_cell", "notes"}

    pptx_path = getattr(presentation, "_pptx_path", None)
    theme_data = get_pptx_theme_summary(pptx_path) if pptx_path else None

    accent_color = RGBColor(0x1F, 0x77, 0xB4)
    if theme_data and 'colors' in theme_data:
        accent1 = theme_data['colors'].get('accent1')
        if accent1:
            try: accent_color = RGBColor.from_string(accent1)
            except Exception: pass

    slides_to_optimize = set()

    for block in blocks:
        slide_index, shape_id = block.get("slide_index"), block.get("shape_id")
        translated_text, source_text = block.get("translated_text", ""), block.get("source_text", "")
        if slide_index is None or shape_id is None or slide_index < 0 or slide_index >= len(presentation.slides):
            continue

        combined_text = f"{source_text}\n\n{translated_text}" if mode == "bilingual" else translated_text
        block_type = block.get("block_type", "textbox")
        slide = presentation.slides[slide_index]
        scale = estimate_scale(source_text, translated_text)
        is_auto_layout = block.get("layout", "auto") in ("auto", "new_slide")

        if block.get("layout") == "new_slide":
            slides_to_optimize.add(slide_index)

        if block_type == "notes":
            if not slide.has_notes_slide: continue
            notes_shape = find_shape_in_shapes(slide.notes_slide.shapes, shape_id)
            if notes_shape and notes_shape.has_text_frame:
                if mode == "bilingual":
                    if not set_bilingual_text(notes_shape.text_frame, source_text, translated_text, auto_size=is_auto_layout, scale=scale, theme_data=theme_data, target_language=target_language, font_mapping=font_mapping):
                        set_text_preserve_format(notes_shape.text_frame, combined_text, auto_size=is_auto_layout, scale=scale)
                else: set_text_preserve_format(notes_shape.text_frame, translated_text, auto_size=is_auto_layout, scale=scale)
            continue

        shape = find_shape_with_id(slide, shape_id)
        if not shape: continue
        
        if block_type == "table_cell" and shape.has_table:
            key = (slide_index, shape_id)
            if key not in table_cell_positions:
                table_cell_positions[key] = iter_table_cells(shape)
                table_cell_index[key] = 0
            idx = table_cell_index[key]
            cells = table_cell_positions[key]
            if idx < len(cells):
                if mode == "bilingual":
                    if not set_bilingual_text(cells[idx], source_text, translated_text, auto_size=is_auto_layout, scale=scale, theme_data=theme_data, target_language=target_language, font_mapping=font_mapping):
                        set_text_preserve_format(cells[idx], combined_text, auto_size=is_auto_layout, scale=scale)
                else: set_text_preserve_format(cells[idx], translated_text, auto_size=is_auto_layout, scale=scale)
                table_cell_index[key] = idx + 1
            continue

        if not shape.has_text_frame: continue
        orig_geom = (shape.left, shape.top, shape.width, shape.height)
        overflow_limit = 2000 if block.get("layout", "auto") == "new_slide" else 400

        if is_auto_layout and len(translated_text) > overflow_limit:
            chunks = split_text_chunks(translated_text, overflow_limit)
            if chunks:
                first = chunks.pop(0)
                if mode == "bilingual": set_bilingual_text(shape.text_frame, source_text, translated_text, auto_size=is_auto_layout, scale=scale, theme_data=theme_data, target_language=target_language, font_mapping=font_mapping)
                else: set_text_preserve_format(shape.text_frame, translated_text, auto_size=is_auto_layout, scale=scale)
                if chunks: add_overflow_textboxes(slide, shape, chunks, capture_font_spec(shape.text_frame), accent_color if mode == "bilingual" else None, presentation.slide_height, target_language=target_language, font_mapping=font_mapping, scale=scale)
            try: shape.left, shape.top, shape.width, shape.height = orig_geom
            except Exception: pass
            continue

        if mode == "bilingual":
            if not set_bilingual_text(shape.text_frame, source_text, translated_text, auto_size=is_auto_layout, scale=scale, theme_data=theme_data, target_language=target_language, font_mapping=font_mapping):
                set_text_preserve_format(shape.text_frame, combined_text, auto_size=is_auto_layout, scale=scale)
        else:
            if translated_text:
                if is_auto_layout: shape.text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
                if not set_bilingual_text(shape.text_frame, "", translated_text, auto_size=is_auto_layout, scale=scale, theme_data=theme_data, target_language=target_language, font_mapping=font_mapping):
                    set_text_preserve_format(shape.text_frame, translated_text, auto_size=is_auto_layout, scale=scale)

        try: shape.left, shape.top, shape.width, shape.height = orig_geom
        except Exception: pass

    for slide_idx in slides_to_optimize:
        if slide_idx < len(presentation.slides):
            fix_title_overlap(presentation.slides[slide_idx])
