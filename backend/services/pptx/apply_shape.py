"""
PPTX Shape Utilities - Shape search and iteration functions.
Extracted from pptx_apply_layout.py for modularity.
"""
from __future__ import annotations

from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.slide import Slide
from pptx.text.text import TextFrame


def _iter_shapes(shapes):
    """Recursively iterate through all shapes including group contents."""
    for shape in shapes:
        yield shape
        try:
            if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                yield from _iter_shapes(shape.shapes)
        except Exception:
            continue


def find_shape_in_shapes(shapes, shape_id: int):
    """Find a shape by ID within a shapes collection."""
    for shape in _iter_shapes(shapes):
        if shape.shape_id == shape_id:
            return shape
    return None


def find_shape_with_id(slide: Slide, shape_id: int):
    """Find a shape by ID within a slide."""
    return find_shape_in_shapes(slide.shapes, shape_id)


def iter_table_cells(shape) -> list[TextFrame]:
    """Iterate through all cells in a table shape."""
    cells = []
    for row in shape.table.rows:
        for cell in row.cells:
            cells.append(cell.text_frame)
    return cells
