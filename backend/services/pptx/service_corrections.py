from __future__ import annotations
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from .apply_layout import find_shape_in_shapes, find_shape_with_id, iter_table_cells
from .text_utils import parse_hex_color, parse_dash_style
from .apply_text import build_corrected_lines, apply_shape_highlight, set_corrected_text, set_text_preserve_format

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
    table_cell_positions = {}
    table_cell_index = {}
    supported_types = {"textbox", "table_cell", "notes"}
    fill_yellow = parse_hex_color(fill_color, RGBColor(0xFF, 0xF1, 0x6A))
    text_red = parse_hex_color(text_color, RGBColor(0xD9, 0x00, 0x00))
    line_purple = parse_hex_color(line_color, RGBColor(0x7B, 0x2C, 0xB9))
    dash_style = parse_dash_style(line_dash) or MSO_LINE_DASH_STYLE.DASH

    for block in blocks:
        if block.get("apply") is False or block.get("selected") is False: continue
        if block.get("block_type") not in supported_types: continue
        translated_text = block.get("translated_text", "")
        if not translated_text: continue
        slide_index, shape_id = block.get("slide_index"), block.get("shape_id")
        if slide_index is None or shape_id is None or slide_index >= len(presentation.slides): continue
        
        slide = presentation.slides[slide_index]
        source_text = block.get("source_text", "")
        lines = build_corrected_lines(source_text, translated_text)

        if block.get("block_type") == "notes":
            if not slide.has_notes_slide: continue
            notes_shape = find_shape_in_shapes(slide.notes_slide.shapes, shape_id)
            if notes_shape and notes_shape.has_text_frame:
                apply_shape_highlight(notes_shape, fill_yellow, line_purple, dash_style)
                if not set_corrected_text(notes_shape.text_frame, lines, text_red):
                    set_text_preserve_format(notes_shape.text_frame, "\n".join(lines))
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
                try:
                    cell = shape.table.cell(idx // len(shape.table.columns), idx % len(shape.table.columns))
                    cell.fill.solid(); cell.fill.fore_color.rgb = fill_yellow
                except Exception: pass
                apply_shape_highlight(shape, fill_yellow, line_purple, dash_style)
                if not set_corrected_text(cells[idx], lines, text_red):
                    set_text_preserve_format(cells[idx], "\n".join(lines))
                table_cell_index[key] = idx + 1
            continue

        if not shape.has_text_frame: continue
        apply_shape_highlight(shape, fill_yellow, line_purple, dash_style)
        if not set_corrected_text(shape.text_frame, lines, text_red):
            set_text_preserve_format(shape.text_frame, "\n".join(lines))

    presentation.save(pptx_out)
