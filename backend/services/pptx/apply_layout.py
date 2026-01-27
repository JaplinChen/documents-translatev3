"""PPTX layout utilities for overflow and title overlap fixes."""
from __future__ import annotations

from typing import Any

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.enum.text import MSO_AUTO_SIZE
from pptx.slide import Slide
from pptx.text.text import TextFrame

def capture_font_spec(text_frame: TextFrame) -> dict[str, Any]:
    """Capture font properties from the first paragraph run."""
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
            ".//{http://schemas.openxmlformats.org/presentationml/2006/main}"
            "pPr"
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
    """Add overflow textboxes when content exceeds original shape."""
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

            # Apply paragraph-level styles
            if font_spec:
                if font_spec.get("alignment") is not None:
                    paragraph.alignment = font_spec["alignment"]
                paragraph.level = font_spec.get("level", 0)

                # Apply XML style if available
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

                # Override with font mapping if needed
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


def fix_title_overlap(slide: Slide) -> None:  # noqa: C901
    """
    Detects if the title overlaps with other content.
    Groups vertically aligned obstacles and moves/scales them together
    to fit between the Title and any Bottom Limit.
    """
    try:
        title_shape = slide.shapes.title if slide.shapes.title else None
        if not title_shape:
            sorted_shapes = sorted(
                [s for s in slide.shapes if s.has_text_frame],
                key=lambda s: s.top,
            )
            if sorted_shapes:
                title_shape = sorted_shapes[0]

        if not title_shape:
            return

        margin_buffer = 50000
        title_bottom = title_shape.top + title_shape.height + margin_buffer
        slide_height = getattr(
            slide.part.presentation,
            "slide_height",
            6858000,
        )

        valid_types = (
            MSO_SHAPE_TYPE.PICTURE,
            MSO_SHAPE_TYPE.GROUP,
            MSO_SHAPE_TYPE.TABLE,
            MSO_SHAPE_TYPE.AUTO_SHAPE,
        )

        obstacles = [
            s
            for s in slide.shapes
            if s.shape_id != title_shape.shape_id
            and s.shape_type in valid_types
        ]

        if not obstacles:
            return

        # Group obstacles into columns based on X-overlap
        columns = []
        sorted_obs = sorted(obstacles, key=lambda s: s.left)

        while sorted_obs:
            current = sorted_obs.pop(0)
            col = [current]
            remaining = []

            for other in sorted_obs:
                overlap_x = (
                    min(
                        current.left + current.width,
                        other.left + other.width,
                    )
                    - max(current.left, other.left)
                )
                is_aligned = False

                if overlap_x > 0:
                    share_pct = overlap_x / min(
                        current.width,
                        other.width,
                    )
                    if share_pct > 0.5:
                        is_aligned = True

                if is_aligned:
                    col.append(other)
                else:
                    remaining.append(other)

            columns.append(col)
            sorted_obs = remaining

        # Process each column
        for col in columns:
            col.sort(key=lambda s: s.top)

            col_top = col[0].top
            col_bottom = col[-1].top + col[-1].height

            if col_top < title_bottom and col_bottom > title_shape.top:
                limit_bottom = slide_height
                col_ids = {s.shape_id for s in col}
                c_left = min(s.left for s in col)
                c_width = max(s.left + s.width for s in col) - c_left

                for potential in slide.shapes:
                    if potential.shape_id in col_ids:
                        continue
                    if potential.shape_id == title_shape.shape_id:
                        continue

                    if potential.top >= col_top:
                        p_overlap = (
                            min(
                                c_left + c_width,
                                potential.left + potential.width,
                            )
                            - max(c_left, potential.left)
                        )
                        if p_overlap > 0 and potential.top < limit_bottom:
                            limit_bottom = potential.top

                margin = 50000
                target_top = title_bottom + margin
                max_frame_height = (limit_bottom - margin) - target_top

                if max_frame_height < 100000:
                    continue

                current_group_height = col_bottom - col_top
                scale = (
                    max_frame_height / current_group_height
                    if current_group_height > max_frame_height
                    else 1.0
                )

                base_top = target_top
                for shape in col:
                    rel_y = shape.top - col_top
                    new_rel_y = int(rel_y * scale)
                    shape.top = base_top + new_rel_y
                    shape.height = int(shape.height * scale)
                    shape.width = int(shape.width * scale)

    except Exception as exc:
        print(f"[LAYOUT_FIX] Error in fix_title_overlap: {exc}", flush=True)
