from __future__ import annotations

from pptx.dml.color import RGBColor

from backend.services.font_manager import estimate_scale

from .apply_layout import add_overflow_textboxes, capture_font_spec
from .apply_shape import find_shape_in_shapes, iter_table_cells
from .apply_text import set_bilingual_text, set_text_preserve_format
from .text_utils import parse_hex_color, split_text_chunks


def get_translated_color(
    theme_data: dict[str, dict[str, str]] | None,
) -> RGBColor:
    default = RGBColor(0x1F, 0x77, 0xB4)
    if not theme_data:
        return default
    accent_hex = theme_data.get("colors", {}).get("accent1")
    if not accent_hex:
        return default
    try:
        return parse_hex_color(accent_hex)
    except Exception:
        return default


def should_process_block(block: dict, supported_types: set[str]) -> bool:
    if block.get("apply") is False or block.get("selected") is False:
        return False
    return block.get("block_type", "textbox") in supported_types


def handle_notes_shape(
    slide,
    shape_id: int,
    source_text: str,
    translated_text: str,
    combined_text: str,
    layout: str,
    target_language: str | None,
    font_mapping: dict[str, list[str]] | None,
    theme_data: dict[str, dict[str, str]] | None,
    scale: float,
) -> None:
    if not slide.has_notes_slide:
        return
    notes_shape = find_shape_in_shapes(slide.notes_slide.shapes, shape_id)
    if not notes_shape or not notes_shape.has_text_frame:
        return

    auto_size = layout == "auto"
    success = set_bilingual_text(
        notes_shape.text_frame,
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
            notes_shape.text_frame,
            combined_text,
            scale=scale,
        )


def handle_table_cell(
    shape,
    slide_index: int,
    shape_id: int,
    block: dict,
    table_cell_positions: dict[tuple[int, int], list],
    table_cell_index: dict[tuple[int, int], int],
    source_text: str,
    translated_text: str,
    combined_text: str,
    layout: str,
    scale: float,
    theme_data: dict[str, dict[str, str]] | None,
    font_mapping: dict[str, list[str]] | None,
    target_language: str | None,
) -> bool:
    if (
        block.get("block_type") != "table_cell"
        or not getattr(shape, "has_table", False)
    ):
        return False

    key = (slide_index, shape_id)
    if key not in table_cell_positions:
        table_cell_positions[key] = iter_table_cells(shape)
        table_cell_index[key] = 0

    current = table_cell_index[key]
    cells = table_cell_positions[key]
    if current >= len(cells):
        return True

    auto_size = layout == "auto"
    cell_frame = cells[current]
    success = set_bilingual_text(
        cell_frame,
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
            cell_frame,
            combined_text,
            scale=scale,
        )

    table_cell_index[key] = current + 1
    return True


def handle_shape_text(
    slide,
    shape,
    layout: str,
    source_text: str,
    translated_text: str,
    combined_text: str,
    scale: float,
    theme_data: dict[str, dict[str, str]] | None,
    target_language: str | None,
    font_mapping: dict[str, list[str]] | None,
    translated_color: RGBColor,
    slide_height: int,
) -> None:
    auto_size = layout == "auto"
    if auto_size and len(translated_text) > 400:
        set_text_preserve_format(shape.text_frame, source_text)
        chunks = split_text_chunks(translated_text, 300)
        add_overflow_textboxes(
            slide,
            shape,
            chunks,
            capture_font_spec(shape.text_frame),
            translated_color,
            slide_height,
        )
        return

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
            scale=scale,
        )


def compute_scale(source_text: str, translated_text: str) -> float:
    return estimate_scale(source_text, translated_text)
