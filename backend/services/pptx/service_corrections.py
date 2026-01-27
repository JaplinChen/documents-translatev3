"""PPTX Chinese correction helpers."""

from __future__ import annotations

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE_DASH_STYLE

from .apply_shape import find_shape_in_shapes, find_shape_with_id, iter_table_cells
from .apply_text import (
    apply_shape_highlight,
    build_corrected_lines,
    set_corrected_text,
    set_text_preserve_format,
)
from .text_utils import parse_dash_style, parse_hex_color

def apply_chinese_corrections(
    pptx_in: str,
    pptx_out: str,
    blocks: list[dict],
    fill_color: str | None = None,
    text_color: str | None = None,
    line_color: str | None = None,
    line_dash: str | None = None,
) -> None:
    presentation = Presentation(pptx_in)
    table_cell_positions: dict[tuple[int, int], list] = {}
    table_cell_index: dict[tuple[int, int], int] = {}

    supported_types = {"textbox", "table_cell", "notes"}
    fill_yellow = parse_hex_color(fill_color, RGBColor(0xFF, 0xF1, 0x6A))
    text_red = parse_hex_color(text_color, RGBColor(0xD9, 0x00, 0x00))
    line_purple = parse_hex_color(line_color, RGBColor(0x7B, 0x2C, 0xB9))
    dash_style = parse_dash_style(line_dash) or MSO_LINE_DASH_STYLE.DASH

    for block in blocks:
        if not _should_process_block(block, supported_types):
            continue

        translated_text = block.get("translated_text", "")
        if not translated_text:
            continue

        slide_index = block.get("slide_index")
        shape_id = block.get("shape_id")
        if (
            slide_index is None
            or shape_id is None
            or slide_index >= len(presentation.slides)
        ):
            continue

        slide = presentation.slides[slide_index]
        source_text = block.get("source_text", "")
        lines = build_corrected_lines(source_text, translated_text)
        combined = "\n".join(lines)

        if block.get("block_type") == "notes":
            _apply_to_notes(
                slide,
                shape_id,
                lines,
                text_red,
                fill_yellow,
                line_purple,
                dash_style,
            )
            continue

        shape = find_shape_with_id(slide, shape_id)
        if not shape:
            continue

        if (
            block.get("block_type") == "table_cell"
            and getattr(shape, "has_table", False)
        ):
            _apply_to_table_cell(
                shape,
                slide_index,
                shape_id,
                table_cell_positions,
                table_cell_index,
                lines,
                combined,
                text_red,
                fill_yellow,
                line_purple,
                dash_style,
            )
            continue

        if not shape.has_text_frame:
            continue

        _apply_highlighting(
            shape,
            lines,
            text_red,
            fill_yellow,
            line_purple,
            dash_style,
        )

    presentation.save(pptx_out)


def _should_process_block(block: dict, supported_types: set[str]) -> bool:
    if block.get("apply") is False or block.get("selected") is False:
        return False
    return block.get("block_type", "textbox") in supported_types


def _apply_to_notes(
    slide,
    shape_id: int,
    lines: list[str],
    text_color: RGBColor,
    fill_color: RGBColor,
    line_color: RGBColor,
    dash_style: MSO_LINE_DASH_STYLE,
) -> None:
    if not slide.has_notes_slide:
        return

    notes_shape = find_shape_in_shapes(slide.notes_slide.shapes, shape_id)
    if not notes_shape or not notes_shape.has_text_frame:
        return

    apply_shape_highlight(notes_shape, fill_color, line_color, dash_style)
    if not set_corrected_text(notes_shape.text_frame, lines, text_color):
        set_text_preserve_format(notes_shape.text_frame, "\n".join(lines))


def _apply_to_table_cell(
    shape,
    slide_index: int,
    shape_id: int,
    table_cell_positions: dict[tuple[int, int], list],
    table_cell_index: dict[tuple[int, int], int],
    lines: list[str],
    combined_text: str,
    text_color: RGBColor,
    fill_color: RGBColor,
    line_color: RGBColor,
    dash_style: MSO_LINE_DASH_STYLE,
) -> None:
    key = (slide_index, shape_id)
    if key not in table_cell_positions:
        table_cell_positions[key] = iter_table_cells(shape)
        table_cell_index[key] = 0

    idx = table_cell_index[key]
    cells = table_cell_positions[key]
    if idx >= len(cells):
        return

    cell_frame = cells[idx]
    try:
        table = shape.table
        row = idx // len(table.columns)
        col = idx % len(table.columns)
        cell = table.cell(row, col)
        cell.fill.solid()
        cell.fill.fore_color.rgb = fill_color
    except Exception:
        pass

    apply_shape_highlight(shape, fill_color, line_color, dash_style)
    if not set_corrected_text(cell_frame, lines, text_color):
        set_text_preserve_format(cell_frame, combined_text, scale=1.0)

    table_cell_index[key] = idx + 1


def _apply_highlighting(
    shape,
    lines: list[str],
    text_color: RGBColor,
    fill_color: RGBColor,
    line_color: RGBColor,
    dash_style: MSO_LINE_DASH_STYLE,
) -> None:
    apply_shape_highlight(shape, fill_color, line_color, dash_style)
    if not set_corrected_text(shape.text_frame, lines, text_color):
        set_text_preserve_format(shape.text_frame, "\n".join(lines))
