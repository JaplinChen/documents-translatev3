from __future__ import annotations

from collections.abc import Iterable

from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_AUTO_SIZE
from pptx.slide import Slide

from backend.services.font_manager import estimate_scale

from .apply_layout import add_overflow_textboxes, capture_font_spec, fix_title_overlap
from .apply_shape import find_shape_in_shapes, find_shape_with_id, iter_table_cells
from .apply_text import set_bilingual_text, set_text_preserve_format
from .text_utils import split_text_chunks
from .xml_core import get_pptx_theme_summary

def _apply_translations_to_presentation(
    presentation,
    blocks: Iterable[dict],
    mode: str = "direct",
    target_language: str | None = None,
    font_mapping: dict[str, list[str]] | None = None,
) -> None:
    table_cell_positions: dict[tuple[int, int], list] = {}
    table_cell_index: dict[tuple[int, int], int] = {}

    pptx_path = getattr(presentation, "_pptx_path", None)
    theme_data = get_pptx_theme_summary(pptx_path) if pptx_path else None
    accent_color = _get_accent_color(theme_data)

    slides_to_optimize: set[int] = set()

    for block in blocks:
        slide_index = block.get("slide_index")
        shape_id = block.get("shape_id")
        if slide_index is None or shape_id is None:
            continue
        if slide_index < 0 or slide_index >= len(presentation.slides):
            continue

        slide = presentation.slides[slide_index]
        scale = estimate_scale(
            block.get("source_text", ""), block.get("translated_text", "")
        )
        is_auto_layout = block.get("layout", "auto") in {"auto", "new_slide"}
        if block.get("layout") == "new_slide":
            slides_to_optimize.add(slide_index)

        combined_text = _compose_text(
            block.get("source_text", ""),
            block.get("translated_text", ""),
            mode,
        )
        block_type = block.get("block_type", "textbox")
        shape = _resolve_shape(slide, shape_id, block_type)
        if shape is None:
            continue

        if _apply_to_notes(
            shape,
            mode,
            scale,
            target_language,
            font_mapping,
            theme_data,
            is_auto_layout,
            block,
            combined_text,
        ):
            continue

        if _apply_table_cell(
            slide,
            shape,
            block,
            table_cell_positions,
            table_cell_index,
            mode,
            scale,
            target_language,
            font_mapping,
            theme_data,
            is_auto_layout,
            combined_text,
        ):
            continue

        if not shape.has_text_frame:
            continue

        orig_geom = (
            shape.left,
            shape.top,
            shape.width,
            shape.height,
        )
        try:
            _apply_text_frame(
                slide,
                shape,
                block,
                mode,
                is_auto_layout,
                scale,
                target_language,
                font_mapping,
                theme_data,
                combined_text,
                accent_color,
                presentation.slide_height,
            )
        finally:
            _reset_shape_geometry(shape, orig_geom)

    _optimize_slides(presentation, slides_to_optimize)


def _get_accent_color(
    theme_data: dict[str, dict[str, str]] | None,
) -> RGBColor:
    default_color = RGBColor(0x1F, 0x77, 0xB4)
    if not theme_data:
        return default_color
    accent_hex = theme_data.get("colors", {}).get("accent1")
    if not accent_hex:
        return default_color
    try:
        return RGBColor.from_string(accent_hex)
    except Exception:
        return default_color


def _compose_text(source_text: str, translated_text: str, mode: str) -> str:
    if mode == "bilingual":
        return f"{source_text}\n\n{translated_text}"
    return translated_text


def _resolve_shape(slide: Slide, shape_id: int, block_type: str):
    if block_type == "notes":
        notes = slide.notes_slide if slide.has_notes_slide else None
        if not notes:
            return None
        return find_shape_in_shapes(notes.shapes, shape_id)
    return find_shape_with_id(slide, shape_id)


def _apply_to_notes(
    shape,
    mode,
    scale,
    target_language,
    font_mapping,
    theme_data,
    auto_size,
    block,
    combined_text,
) -> bool:
    if not shape or not shape.has_text_frame:
        return False
    block_type = block.get("block_type", "textbox")
    if block_type != "notes":
        return False

    source_text = block.get("source_text", "")
    translated_text = block.get("translated_text", "")
    if mode == "bilingual":
        success = set_bilingual_text(
            shape.text_frame,
            source_text,
            translated_text,
            auto_size=auto_size,
            scale=scale,
            theme_data=theme_data,
            target_language=target_language,
            font_mapping=font_mapping,
        )
        if not success:
            set_text_preserve_format(
                shape.text_frame,
                combined_text,
                auto_size=auto_size,
                scale=scale,
            )
    else:
        set_text_preserve_format(
            shape.text_frame,
            translated_text,
            auto_size=auto_size,
            scale=scale,
        )
    return True


def _apply_table_cell(
    slide,
    shape,
    block,
    table_cell_positions,
    table_cell_index,
    mode,
    scale,
    target_language,
    font_mapping,
    theme_data,
    is_auto_layout,
    combined_text,
) -> bool:
    if (
        block.get("block_type", "textbox") != "table_cell"
        or not getattr(shape, "has_table", False)
    ):
        return False

    key = (block.get("slide_index"), block.get("shape_id"))
    if key not in table_cell_positions:
        table_cell_positions[key] = iter_table_cells(shape)
        table_cell_index[key] = 0

    current_index = table_cell_index[key]
    cells = table_cell_positions[key]
    if current_index >= len(cells):
        return True

    target_cell = cells[current_index]
    source_text = block.get("source_text", "")
    translated_text = block.get("translated_text", "")
    if mode == "bilingual":
        success = set_bilingual_text(
            target_cell,
            source_text,
            translated_text,
            auto_size=is_auto_layout,
            scale=scale,
            theme_data=theme_data,
            target_language=target_language,
            font_mapping=font_mapping,
        )
        if not success:
            set_text_preserve_format(
                target_cell,
                combined_text,
                auto_size=is_auto_layout,
                scale=scale,
            )
    else:
        set_text_preserve_format(
            target_cell,
            translated_text,
            auto_size=is_auto_layout,
            scale=scale,
        )

    table_cell_index[key] = current_index + 1
    return True


def _apply_text_frame(
    slide,
    shape,
    block,
    mode,
    auto_layout,
    scale,
    target_language,
    font_mapping,
    theme_data,
    combined_text,
    accent_color,
    slide_height,
):
    translated_text = block.get("translated_text", "")
    overflow_limit = (
        2000 if block.get("layout", "auto") == "new_slide" else 400
    )
    if auto_layout and len(translated_text) > overflow_limit:
        chunk_limit = split_text_chunks(translated_text, overflow_limit)
        if chunk_limit:
            chunk_limit.pop(0)
            if mode == "bilingual":
                set_bilingual_text(
                    shape.text_frame,
                    block.get("source_text", ""),
                    translated_text,
                    auto_size=auto_layout,
                    scale=scale,
                    theme_data=theme_data,
                    target_language=target_language,
                    font_mapping=font_mapping,
                )
            else:
                set_text_preserve_format(
                    shape.text_frame,
                    translated_text,
                    auto_size=auto_layout,
                    scale=scale,
                )
            if chunk_limit:
                add_overflow_textboxes(
                    slide,
                    shape,
                    chunk_limit,
                    capture_font_spec(shape.text_frame),
                    accent_color if mode == "bilingual" else None,
                    slide_height,
                    target_language=target_language,
                    font_mapping=font_mapping,
                    scale=scale,
                )
        return

    if mode == "bilingual":
        success = set_bilingual_text(
            shape.text_frame,
            block.get("source_text", ""),
            translated_text,
            auto_size=auto_layout,
            scale=scale,
            theme_data=theme_data,
            target_language=target_language,
            font_mapping=font_mapping,
        )
        if not success:
            set_text_preserve_format(
                shape.text_frame,
                combined_text,
                auto_size=auto_layout,
                scale=scale,
            )
    else:
        if translated_text:
            if auto_layout:
                shape.text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
            success = set_bilingual_text(
                shape.text_frame,
                "",
                translated_text,
                auto_size=auto_layout,
                scale=scale,
                theme_data=theme_data,
                target_language=target_language,
                font_mapping=font_mapping,
            )
            if not success:
                set_text_preserve_format(
                    shape.text_frame,
                    translated_text,
                    auto_size=auto_layout,
                    scale=scale,
                )


def _reset_shape_geometry(shape, geom):
    try:
        shape.left, shape.top, shape.width, shape.height = geom
    except Exception:
        pass


def _optimize_slides(presentation, slides_to_optimize: set[int]) -> None:
    for slide_idx in slides_to_optimize:
        if slide_idx < len(presentation.slides):
            fix_title_overlap(presentation.slides[slide_idx])
