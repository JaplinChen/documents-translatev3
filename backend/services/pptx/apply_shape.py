"""Shape helpers extracted from pptx_apply_layout."""

from __future__ import annotations

from collections.abc import Generator, Iterable

from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.slide import Slide
from pptx.text.text import TextFrame

def _iter_shapes(shapes: Iterable) -> Generator:
    """Recursively yield shapes, including groups."""
    for shape in shapes:
        yield shape
        if (
            hasattr(shape, "shape_type")
            and shape.shape_type == MSO_SHAPE_TYPE.GROUP
        ):
            try:
                yield from _iter_shapes(shape.shapes)
            except Exception:
                continue


def find_shape_in_shapes(shapes: Iterable, shape_id: int):
    """Return the shape matching <shape_id> or None."""
    return next(
        (
            shape
            for shape in _iter_shapes(shapes)
            if shape.shape_id == shape_id
        ),
        None,
    )


def find_shape_with_id(slide: Slide, shape_id: int):
    """Return a shape from <slide> by ID."""
    return find_shape_in_shapes(slide.shapes, shape_id)


def iter_table_cells(shape) -> list[TextFrame]:
    """Return text frames stored in a table shape."""
    frames: list[TextFrame] = []
    table = getattr(shape, "table", None)
    if table is None:
        return frames
    for row in table.rows:
        for cell in row.cells:
            frames.append(cell.text_frame)
    return frames
