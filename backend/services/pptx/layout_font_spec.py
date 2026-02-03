from __future__ import annotations

from typing import Any

from pptx.text.text import TextFrame


def capture_font_spec(text_frame: TextFrame) -> dict[str, Any]:
    spec: dict[str, Any] = {
        "name": None,
        "size": None,
        "bold": None,
        "italic": None,
        "underline": None,
        "color": None,
        "alignment": None,
        "level": 0,
        "pPr_xml": None,
    }

    if not text_frame.paragraphs:
        return spec

    paragraph = text_frame.paragraphs[0]
    for candidate in text_frame.paragraphs:
        if candidate.text and candidate.text.strip():
            paragraph = candidate
            break

    spec["alignment"] = paragraph.alignment
    spec["level"] = paragraph.level

    try:
        from lxml import etree

        parent = paragraph._p
        p_pr_xml = parent.find(
            ".//{http://schemas.openxmlformats.org/presentationml/2006/main}pPr"
        )
        if p_pr_xml is None:
            p_pr_xml = parent.find(
                ".//{http://schemas.openxmlformats.org/drawingml/2006/main}pPr"
            )
        if p_pr_xml is not None:
            spec["pPr_xml"] = etree.tostring(p_pr_xml)
    except Exception:
        pass

    if paragraph.runs:
        run = paragraph.runs[0]
        spec.update(
            name=run.font.name,
            size=run.font.size,
            bold=run.font.bold,
            italic=run.font.italic,
            underline=run.font.underline,
        )
        try:
            spec["color"] = run.font.color.rgb
        except Exception:
            pass

    return spec
