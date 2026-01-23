from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.slide import Slide
from pptx.table import _Cell
from pptx.text.text import TextFrame

from backend.contracts import make_block
from backend.services.extract_utils import is_numeric_only, is_technical_terms_only


def _text_frame_to_text(text_frame: TextFrame) -> str:
    paragraphs = [paragraph.text for paragraph in text_frame.paragraphs]
    return "\n".join(paragraphs).strip()


def _iter_shapes(shapes) -> Iterable:
    for shape in shapes:
        yield shape
        try:
            if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                yield from _iter_shapes(shape.shapes)
        except Exception:
            continue


def emu_to_points(emu: int | float) -> float:
    """Convert EMU to Points (72 points per inch). 1 Point = 12700 EMUs."""
    return float(emu) / 12700.0


def _iter_textbox_blocks(slide: Slide, slide_index: int, seen_ids: set[int]) -> Iterable[dict]:
    for shape in _iter_shapes(slide.shapes):
        try:
            if not shape.has_text_frame or shape.has_table:
                continue
            if shape.shape_id in seen_ids:
                continue
            text = _text_frame_to_text(shape.text_frame)
        except Exception:
            continue
        if not text or is_numeric_only(text) or is_technical_terms_only(text):
            continue
        
        seen_ids.add(shape.shape_id)
        # Extract layout info
        x = emu_to_points(shape.left)
        y = emu_to_points(shape.top)
        w = emu_to_points(shape.width)
        h = emu_to_points(shape.height)

        yield make_block(slide_index, shape.shape_id, "textbox", text, x=x, y=y, width=w, height=h)


def _cell_to_text(cell: _Cell) -> str:
    return _text_frame_to_text(cell.text_frame)


def _iter_table_blocks(slide: Slide, slide_index: int) -> Iterable[dict]:
    for shape in _iter_shapes(slide.shapes):
        if not shape.has_table:
            continue
        
        # Table position (same for all cells in this table for simplification in preview)
        tx = emu_to_points(shape.left)
        ty = emu_to_points(shape.top)
        tw = emu_to_points(shape.width)
        th = emu_to_points(shape.height)

        for row in shape.table.rows:
            for cell in row.cells:
                text = _cell_to_text(cell)
                if not text or is_numeric_only(text) or is_technical_terms_only(text):
                    continue
                yield make_block(slide_index, shape.shape_id, "table_cell", text, x=tx, y=ty, width=tw, height=th)


def _iter_notes_blocks(slide: Slide, slide_index: int) -> Iterable[dict]:
    if not slide.has_notes_slide:
        return
    for shape in _iter_shapes(slide.notes_slide.shapes):
        try:
            if not shape.has_text_frame:
                continue
            text = _text_frame_to_text(shape.text_frame)
        except Exception:
            continue
        if not text or is_numeric_only(text) or is_technical_terms_only(text):
            continue
        
        # Notes position
        x = emu_to_points(shape.left)
        y = emu_to_points(shape.top)
        w = emu_to_points(shape.width)
        h = emu_to_points(shape.height)

        yield make_block(slide_index, shape.shape_id, "notes", text, x=x, y=y, width=w, height=h)


def extract_blocks(pptx_path: str) -> dict:
    presentation = Presentation(pptx_path)
    blocks: list[dict] = []
    
    # Get slide dimensions in Points
    slide_width = emu_to_points(presentation.slide_width)
    slide_height = emu_to_points(presentation.slide_height)

    for slide_index, slide in enumerate(presentation.slides):
        seen_ids = set()
        blocks.extend(_iter_textbox_blocks(slide, slide_index, seen_ids))
        blocks.extend(_iter_table_blocks(slide, slide_index))
        blocks.extend(_iter_notes_blocks(slide, slide_index))
    
    return {
        "blocks": blocks,
        "slide_width": slide_width,
        "slide_height": slide_height
    }

