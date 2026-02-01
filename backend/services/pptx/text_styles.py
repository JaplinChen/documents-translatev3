from __future__ import annotations

from typing import Any

from lxml import etree
from pptx.text.text import TextFrame

from backend.services.font_manager import clone_font_props


def capture_full_frame_styles(
    text_frame: TextFrame,
) -> list[dict[str, Any]]:
    """Return paragraph-level metadata for a text frame."""
    styles: list[dict[str, Any]] = []
    for paragraph in text_frame.paragraphs:
        styles.append(_capture_paragraph_style(paragraph))

    _consolidate_empty_spacing(styles)
    return styles


def _capture_paragraph_style(paragraph) -> dict[str, Any]:
    p_pr_xml = None
    try:
        parent = paragraph._p
        p_pr_xml = parent.find(".//{http://schemas.openxmlformats.org/presentationml/2006/main}pPr")
        if p_pr_xml is None:
            p_pr_xml = parent.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}pPr")
        if p_pr_xml is not None:
            p_pr_xml = etree.tostring(p_pr_xml)
    except Exception:
        p_pr_xml = None

    runs = paragraph.runs
    primary_font = runs[0].font if runs else None

    return {
        "level": paragraph.level,
        "alignment": paragraph.alignment,
        "space_before": paragraph.space_before,
        "space_after": paragraph.space_after,
        "line_spacing": paragraph.line_spacing,
        "font_obj": primary_font,
        "bold": primary_font.bold if primary_font else None,
        "italic": primary_font.italic if primary_font else None,
        "underline": primary_font.underline if primary_font else None,
        "has_text": bool(paragraph.text and paragraph.text.strip()),
        "pPr_xml": p_pr_xml,
    }


def _consolidate_empty_spacing(styles: list[dict[str, Any]]) -> None:
    pending_before = 0
    last_text_idx = -1
    for i, style in enumerate(styles):
        if style["has_text"]:
            if pending_before > 0:
                current_before = style["space_before"] or 0
                style["space_before"] = current_before + pending_before
                pending_before = 0
            last_text_idx = i
            continue

        para_height = _estimate_empty_paragraph_height(style)
        extra_spacing = (style["space_before"] or 0) + (style["space_after"] or 0) + para_height
        if last_text_idx >= 0:
            prev_after = styles[last_text_idx]["space_after"] or 0
            styles[last_text_idx]["space_after"] = prev_after + extra_spacing
        else:
            pending_before += extra_spacing


def _estimate_empty_paragraph_height(style: dict[str, Any]) -> int:
    default_size = 18 * 12700
    font_size = default_size
    if style["font_obj"] and style["font_obj"].size:
        font_size = style["font_obj"].size

    line_spacing = style["line_spacing"] or 1.0
    is_points = isinstance(line_spacing, (int, float)) and line_spacing > 100
    spacing_value = line_spacing if is_points else font_size * line_spacing
    return int(spacing_value)


def apply_paragraph_style(
    paragraph,
    p_style: dict[str, Any],
    scale: float = 1.0,
    target_language: str | None = None,
    font_mapping: dict[str, list[str]] | None = None,
) -> None:
    """Apply recorded style values to a live paragraph."""
    try:
        p_pr_xml_bytes = p_style.get("pPr_xml")
        if p_pr_xml_bytes:
            _apply_xml_style(paragraph, p_pr_xml_bytes)

        paragraph.level = p_style.get("level", 0)
        paragraph.alignment = p_style.get("alignment")
        if p_style.get("space_before") is not None:
            paragraph.space_before = p_style["space_before"]
        if p_style.get("space_after") is not None:
            paragraph.space_after = p_style["space_after"]
        if p_style.get("line_spacing") is not None:
            paragraph.line_spacing = p_style["line_spacing"]

        source_font = p_style.get("font_obj")
        if source_font and paragraph.runs:
            clone_font_props(
                source_font,
                paragraph.runs[0].font,
                target_language=target_language,
                font_mapping=font_mapping,
            )
            if scale != 1.0 and getattr(paragraph.runs[0].font, "size", None):
                paragraph.runs[0].font.size = int(paragraph.runs[0].font.size * scale)
    except Exception:
        pass


def _apply_xml_style(paragraph, p_pr_xml_bytes: bytes) -> None:
    try:
        target_p = paragraph._p
        new_p_pr = etree.fromstring(p_pr_xml_bytes)
        old_p_pr = target_p.find(
            ".//{http://schemas.openxmlformats.org/presentationml/2006/main}pPr"
        )
        if old_p_pr is None:
            old_p_pr = target_p.find(
                ".//{http://schemas.openxmlformats.org/drawingml/2006/main}pPr"
            )
        if old_p_pr is not None:
            target_p.replace(old_p_pr, new_p_pr)
        else:
            target_p.insert(0, new_p_pr)
    except Exception:
        pass
