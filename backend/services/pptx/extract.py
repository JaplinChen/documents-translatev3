from __future__ import annotations

import re
from collections.abc import Iterable

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.slide import Slide
from pptx.table import _Cell
from pptx.text.text import TextFrame

from backend.contracts import make_block
from backend.services.extract_utils import (
    is_garbage_text,
    is_numeric_only,
    is_technical_terms_only,
)

def _safe_get_shape_type(shape) -> int | None:
    try:
        return getattr(shape, "shape_type", None)
    except Exception:
        return None


def _safe_has_text_frame(shape) -> bool:
    try:
        return getattr(shape, "has_text_frame", False)
    except Exception:
        return False


def _safe_has_table(shape) -> bool:
    try:
        return getattr(shape, "has_table", False)
    except Exception:
        return False


# Pre-compile regex for performance
_A_T_RE = re.compile(r"<a:t[^>]*>(.*?)</a:t>", re.DOTALL)
_XML_TAG_RE = re.compile(r"<[^>]+>")


def _extract_complex_text(shape) -> list[str]:
    """Fallback extraction for SmartArt/Charts using XML."""
    texts = []
    try:
        # Some shapes might not have .element or .xml
        if not hasattr(shape, "element") or not hasattr(shape.element, "xml"):
            return []

        xml_str = shape.element.xml
        tags = _A_T_RE.findall(xml_str)
        for t in tags:
            clean_t = _XML_TAG_RE.sub("", t).strip()
            if (
                clean_t
                and not is_numeric_only(clean_t)
                and not is_technical_terms_only(clean_t)
            ):
                texts.append(clean_t)
    except Exception:
        pass
    return list(dict.fromkeys(texts))  # Unique values


def _text_frame_to_text(text_frame: TextFrame) -> str:
    paragraphs = [paragraph.text for paragraph in text_frame.paragraphs]
    return "\n".join(paragraphs).strip()


def _iter_shapes(shapes) -> Iterable:
    if shapes is None:
        return
    for shape in shapes:
        yield shape
        try:
            stype = _safe_get_shape_type(shape)
            if stype == MSO_SHAPE_TYPE.GROUP:
                yield from _iter_shapes(shape.shapes)
        except Exception:
            continue


def emu_to_points(emu: int | float | None) -> float:
    """Convert EMU to Points (72 points per inch). 1 Point = 12700 EMUs."""
    if emu is None:
        return 0.0
    try:
        return float(emu) / 12700.0
    except (ValueError, TypeError):
        return 0.0


def _iter_textbox_blocks(  # noqa: C901
    slide: Slide,
    slide_index: int,
    seen_ids: set[int],
) -> Iterable[dict]:
    for shape in _iter_shapes(slide.shapes):
        try:
            if not _safe_has_text_frame(shape) or _safe_has_table(shape):
                continue
            if shape.shape_id in seen_ids:
                continue
            text = _text_frame_to_text(shape.text_frame)
        except Exception:
            continue
        if (
            not text
            or is_numeric_only(text)
            or is_technical_terms_only(text)
            or is_garbage_text(text)
        ):
            continue

        seen_ids.add(shape.shape_id)
        # Extract layout info
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

    # Secondary pass for SmartArt/Charts that don't have standard text_frame
    for shape in _iter_shapes(slide.shapes):
        try:
            sid = getattr(shape, "shape_id", None)
            if sid is None or sid in seen_ids:
                continue
            stype = _safe_get_shape_type(shape)
            if stype in (
                MSO_SHAPE_TYPE.GRAPHIC_FRAME,
                MSO_SHAPE_TYPE.SMART_ART,
                MSO_SHAPE_TYPE.CHART,
            ):
                complex_texts = _extract_complex_text(shape)
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


def _cell_to_text(cell: _Cell) -> str:
    return _text_frame_to_text(cell.text_frame)


def _iter_table_blocks(slide: Slide, slide_index: int) -> Iterable[dict]:
    for shape in _iter_shapes(slide.shapes):
        try:
            if not _safe_has_table(shape):
                continue

            # Table position
            tx = emu_to_points(getattr(shape, "left", 0))
            ty = emu_to_points(getattr(shape, "top", 0))
            tw = emu_to_points(getattr(shape, "width", 0))
            th = emu_to_points(getattr(shape, "height", 0))

            for row in shape.table.rows:
                for cell in row.cells:
                    try:
                        text = _cell_to_text(cell)
                        if (
                            not text
                            or is_numeric_only(text)
                            or is_technical_terms_only(text)
                            or is_garbage_text(text)
                        ):
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


def _iter_notes_blocks(slide: Slide, slide_index: int) -> Iterable[dict]:
    try:
        if not getattr(slide, "has_notes_slide", False):
            return
        if slide.notes_slide is None:
            return
    except Exception:
        return

    for shape in _iter_shapes(slide.notes_slide.shapes):
        try:
            if not _safe_has_text_frame(shape):
                continue
            text = _text_frame_to_text(shape.text_frame)
            if (
                not text
                or is_numeric_only(text)
                or is_technical_terms_only(text)
                or is_garbage_text(text)
            ):
                continue

            # Notes position
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


def _iter_master_blocks(presentation: Presentation) -> Iterable[dict]:
    """Extract text from all slide masters."""
    try:
        masters = getattr(presentation, "slide_masters", [])
    except Exception:
        return

    for master_idx, master in enumerate(masters):
        try:
            for shape in _iter_shapes(master.shapes):
                try:
                    if not _safe_has_text_frame(shape):
                        continue
                    text = _text_frame_to_text(shape.text_frame)
                    if (
                        not text
                        or is_numeric_only(text)
                        or is_technical_terms_only(text)
                        or is_garbage_text(text)
                    ):
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

    # Add masters
    blocks.extend(_iter_master_blocks(presentation))

    return {
        "blocks": blocks,
        "slide_width": slide_width,
        "slide_height": slide_height,
    }
