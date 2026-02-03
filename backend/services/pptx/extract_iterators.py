from __future__ import annotations

from collections.abc import Iterable

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.slide import Slide
from pptx.table import _Cell

from backend.contracts import make_block

from .extract_helpers import (
    emu_to_points,
    extract_complex_text,
    iter_shapes,
    safe_get_shape_type,
    safe_has_table,
    safe_has_text_frame,
    should_skip_text,
    text_frame_to_text,
)


def _cell_to_text(cell: _Cell) -> str:
    return text_frame_to_text(cell.text_frame)


def iter_textbox_blocks(
    slide: Slide,
    slide_index: int,
    seen_ids: set[int],
) -> Iterable[dict]:
    for shape in iter_shapes(slide.shapes):
        try:
            if not safe_has_text_frame(shape) or safe_has_table(shape):
                continue
            if shape.shape_id in seen_ids:
                continue
            text = text_frame_to_text(shape.text_frame)
        except Exception:
            continue
        if should_skip_text(text):
            continue

        seen_ids.add(shape.shape_id)
        x = emu_to_points(getattr(shape, "left", 0))
        y = emu_to_points(getattr(shape, "top", 0))
        w = emu_to_points(getattr(shape, "width", 0))
        h = emu_to_points(getattr(shape, "height", 0))

        yield make_block(
            slide_index,
            shape.shape_id,
            "textbox",
            text,
            x=x,
            y=y,
            width=w,
            height=h,
        )

    for shape in iter_shapes(slide.shapes):
        try:
            sid = getattr(shape, "shape_id", None)
            if sid is None or sid in seen_ids:
                continue
            stype = safe_get_shape_type(shape)
            if stype in (
                MSO_SHAPE_TYPE.GRAPHIC_FRAME,
                MSO_SHAPE_TYPE.SMART_ART,
                MSO_SHAPE_TYPE.CHART,
            ):
                complex_texts = extract_complex_text(shape)
                if complex_texts:
                    seen_ids.add(sid)
                    combined_text = "\n".join(complex_texts)
                    x = emu_to_points(getattr(shape, "left", 0))
                    y = emu_to_points(getattr(shape, "top", 0))
                    w = emu_to_points(getattr(shape, "width", 0))
                    h = emu_to_points(getattr(shape, "height", 0))
                    yield make_block(
                        slide_index,
                        sid,
                        "complex_graphic",
                        combined_text,
                        x=x,
                        y=y,
                        width=w,
                        height=h,
                    )
        except Exception:
            continue


def iter_table_blocks(slide: Slide, slide_index: int) -> Iterable[dict]:
    for shape in iter_shapes(slide.shapes):
        try:
            if not safe_has_table(shape):
                continue

            tx = emu_to_points(getattr(shape, "left", 0))
            ty = emu_to_points(getattr(shape, "top", 0))
            tw = emu_to_points(getattr(shape, "width", 0))
            th = emu_to_points(getattr(shape, "height", 0))

            for row in shape.table.rows:
                for cell in row.cells:
                    try:
                        text = _cell_to_text(cell)
                        if should_skip_text(text):
                            continue
                        yield make_block(
                            slide_index,
                            shape.shape_id,
                            "table_cell",
                            text,
                            x=tx,
                            y=ty,
                            width=tw,
                            height=th,
                        )
                    except Exception:
                        continue
        except Exception:
            continue


def iter_notes_blocks(slide: Slide, slide_index: int) -> Iterable[dict]:
    try:
        if not getattr(slide, "has_notes_slide", False):
            return
        if slide.notes_slide is None:
            return
    except Exception:
        return

    for shape in iter_shapes(slide.notes_slide.shapes):
        try:
            if not safe_has_text_frame(shape):
                continue
            text = text_frame_to_text(shape.text_frame)
            if should_skip_text(text):
                continue

            x = emu_to_points(getattr(shape, "left", 0))
            y = emu_to_points(getattr(shape, "top", 0))
            w = emu_to_points(getattr(shape, "width", 0))
            h = emu_to_points(getattr(shape, "height", 0))

            yield make_block(
                slide_index,
                getattr(shape, "shape_id", 0),
                "notes",
                text,
                x=x,
                y=y,
                width=w,
                height=h,
            )
        except Exception:
            continue


def iter_master_blocks(presentation: Presentation) -> Iterable[dict]:
    try:
        masters = getattr(presentation, "slide_masters", [])
    except Exception:
        return

    for master_idx, master in enumerate(masters):
        try:
            for shape in iter_shapes(master.shapes):
                try:
                    if not safe_has_text_frame(shape):
                        continue
                    text = text_frame_to_text(shape.text_frame)
                    if should_skip_text(text):
                        continue

                    sid = getattr(shape, "shape_id", 0)
                    shape_id = f"m{master_idx}_{sid}"
                    yield make_block(
                        -1,
                        shape_id,
                        "master",
                        text,
                        x=0.0,
                        y=0.0,
                        width=500,
                        height=50,
                    )
                except Exception:
                    continue
        except Exception:
            continue
