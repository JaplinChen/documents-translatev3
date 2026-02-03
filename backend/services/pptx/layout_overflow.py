from __future__ import annotations

from typing import Any

from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_AUTO_SIZE
from pptx.slide import Slide


def add_overflow_textboxes(  # noqa: C901
    slide: Slide,
    base_shape,
    chunks: list[str],
    font_spec: dict[str, Any] | None,
    translated_color: RGBColor | None = None,
    max_bottom: int = 0,
    target_language: str | None = None,
    font_mapping: dict[str, list[str]] | None = None,
    scale: float = 1.0,
) -> None:
    if not chunks:
        return
    top = base_shape.top
    height = base_shape.height
    margin = int(height * 0.1)
    for index, chunk in enumerate(chunks):
        next_top = top + height + margin + index * (height + margin)
        if next_top + height > max_bottom:
            break
        box = slide.shapes.add_textbox(
            base_shape.left,
            next_top,
            base_shape.width,
            height,
        )
        text_frame = box.text_frame
        text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
        text_frame.clear()
        for line_index, line in enumerate(chunk.split("\n")):
            paragraph = (
                text_frame.paragraphs[0]
                if line_index == 0
                else text_frame.add_paragraph()
            )
            paragraph.text = line

            if font_spec:
                if font_spec.get("alignment") is not None:
                    paragraph.alignment = font_spec["alignment"]
                paragraph.level = font_spec.get("level", 0)

                if font_spec.get("pPr_xml"):
                    try:
                        from lxml import etree

                        target_p = paragraph._p
                        new_p_pr = etree.fromstring(font_spec["pPr_xml"])

                        old_p_pr = target_p.find(
                            ".//{http://schemas.openxmlformats.org/"
                            "presentationml/2006/main}pPr"
                        )
                        if old_p_pr is None:
                            old_p_pr = target_p.find(
                                ".//{http://schemas.openxmlformats.org/"
                                "drawingml/2006/main}pPr"
                            )

                        if old_p_pr is not None:
                            target_p.replace(old_p_pr, new_p_pr)
                        else:
                            target_p.insert(0, new_p_pr)
                    except Exception:
                        pass

            if paragraph.runs:
                run = paragraph.runs[0]
                if font_spec:
                    if font_spec.get("name"):
                        run.font.name = font_spec["name"]
                    if font_spec.get("size"):
                        final_size = font_spec["size"]
                        if scale != 1.0:
                            final_size = int(final_size * scale)
                        run.font.size = final_size

                    if font_spec.get("bold") is not None:
                        run.font.bold = font_spec["bold"]
                    if font_spec.get("italic") is not None:
                        run.font.italic = font_spec["italic"]
                    if font_spec.get("underline") is not None:
                        run.font.underline = font_spec["underline"]

                    if font_spec.get("color"):
                        try:
                            run.font.color.rgb = font_spec["color"]
                        except Exception:
                            pass

                if target_language or font_mapping:
                    from backend.services.font_manager import clone_font_props

                    clone_font_props(
                        run.font,
                        run.font,
                        target_language=target_language,
                        font_mapping=font_mapping,
                    )

                if translated_color:
                    try:
                        run.font.color.rgb = translated_color
                    except Exception:
                        pass
