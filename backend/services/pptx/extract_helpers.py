from __future__ import annotations

import re
from collections.abc import Iterable

from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.text.text import TextFrame

from backend.services.extract_utils import (
    is_exact_term_match,
    is_garbage_text,
    is_numeric_only,
    is_symbol_only,
    is_technical_terms_only,
)


def safe_get_shape_type(shape) -> int | None:
    try:
        return getattr(shape, "shape_type", None)
    except Exception:
        return None


def safe_has_text_frame(shape) -> bool:
    try:
        return getattr(shape, "has_text_frame", False)
    except Exception:
        return False


def safe_has_table(shape) -> bool:
    try:
        return getattr(shape, "has_table", False)
    except Exception:
        return False


_A_T_RE = re.compile(r"<a:t[^>]*>(.*?)</a:t>", re.DOTALL)
_XML_TAG_RE = re.compile(r"<[^>]+>")


def extract_complex_text(shape) -> list[str]:
    texts = []
    try:
        if not hasattr(shape, "element") or not hasattr(shape.element, "xml"):
            return []

        xml_str = shape.element.xml
        tags = _A_T_RE.findall(xml_str)
        for t in tags:
            clean_t = _XML_TAG_RE.sub("", t).strip()
            if (
                clean_t
                and not is_numeric_only(clean_t)
                and not is_exact_term_match(clean_t)
                and not is_technical_terms_only(clean_t)
            ):
                texts.append(clean_t)
    except Exception:
        pass
    return list(dict.fromkeys(texts))


def text_frame_to_text(text_frame: TextFrame) -> str:
    paragraphs = [paragraph.text for paragraph in text_frame.paragraphs]
    return "\n".join(paragraphs).strip()


def iter_shapes(shapes) -> Iterable:
    if shapes is None:
        return
    for shape in shapes:
        yield shape
        try:
            stype = safe_get_shape_type(shape)
            if stype == MSO_SHAPE_TYPE.GROUP:
                yield from iter_shapes(shape.shapes)
        except Exception:
            continue


def emu_to_points(emu: int | float | None) -> float:
    if emu is None:
        return 0.0
    try:
        return float(emu) / 12700.0
    except (ValueError, TypeError):
        return 0.0


def should_skip_text(text: str) -> bool:
    return (
        not text
        or is_numeric_only(text)
        or is_symbol_only(text)
        or is_exact_term_match(text)
        or is_technical_terms_only(text)
        or is_garbage_text(text)
    )
