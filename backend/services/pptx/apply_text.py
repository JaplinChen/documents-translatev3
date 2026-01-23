from __future__ import annotations
from typing import Any
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.text import MSO_AUTO_SIZE
from pptx.text.text import TextFrame

from backend.services.font_manager import contains_cjk
from .text_utils import sanitize_xml_text, CJK_SPACE_PATTERN
from .text_styles import capture_full_frame_styles, apply_paragraph_style

def apply_shape_highlight(shape: Any, fill_color: RGBColor|None=None, line_color: RGBColor|None=None, dash_style: MSO_LINE_DASH_STYLE|None=None) -> None:
    if fill_color:
        try: shape.fill.solid(); shape.fill.fore_color.rgb = fill_color
        except Exception: pass
    if line_color:
        try: shape.line.color.rgb = line_color
        except Exception: pass
    if dash_style:
        try: shape.line.dash_style = dash_style
        except Exception: pass

def set_text_preserve_format(text_frame: TextFrame, new_text: str, auto_size: bool=False, scale: float=1.0) -> None:
    """Sets text while preserving original paragraph styles and applying Auto-fit logic."""
    try:
        new_text = sanitize_xml_text(new_text)
        para_styles = capture_full_frame_styles(text_frame)
        content_styles = [s for s in para_styles if s.get("has_text")]
        if not content_styles: content_styles = para_styles

        if auto_size: text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
        text_frame.clear()
        lines = [l for l in new_text.split("\n") if l.strip()]
        for index, line in enumerate(lines):
            paragraph = text_frame.paragraphs[0] if index == 0 else text_frame.add_paragraph()
            paragraph.text = line
            style_idx = min(index, len(content_styles) - 1) if content_styles else -1
            if style_idx >= 0:
                apply_paragraph_style(paragraph, content_styles[style_idx], scale=scale)
    except Exception:
        try:
            if auto_size: text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
            text_frame.clear(); text_frame.text = new_text
        except Exception: pass

def apply_cjk_line_breaking(text: str) -> str:
    if not contains_cjk(text): return text
    return CJK_SPACE_PATTERN.sub(r'\1\2', text)

def build_corrected_lines(source_text: str, translated_text: str) -> list[str]:
    non_cjk_lines = [l for l in source_text.split("\n") if l.strip() and not contains_cjk(l)]
    translated_lines = [apply_cjk_line_breaking(l) for l in translated_text.split("\n")] if translated_text else []
    if non_cjk_lines: return non_cjk_lines + [""] + translated_lines
    return translated_lines

def set_bilingual_text(text_frame: TextFrame, source_text: str, translated_text: str, auto_size: bool=False, scale: float=1.0, theme_data: dict[str, Any]|None=None, target_language: str|None=None, font_mapping: dict[str, list[str]]|None=None) -> bool:
    source_text, translated_text = sanitize_xml_text(source_text), sanitize_xml_text(translated_text)
    try:
        para_styles = capture_full_frame_styles(text_frame)
        content_styles = [s for s in para_styles if s.get("has_text")]
        if not content_styles: content_styles = para_styles

        if auto_size: text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
        text_frame.clear()
        source_lines = [l for l in source_text.strip().split("\n") if l.strip()]
        for index, line in enumerate(source_lines):
            paragraph = text_frame.paragraphs[0] if index == 0 else text_frame.add_paragraph()
            paragraph.text = line
            style_idx = min(index, len(content_styles) - 1) if content_styles else -1
            if style_idx >= 0:
                apply_paragraph_style(paragraph, content_styles[style_idx], scale=scale)
        if source_lines and translated_text.strip():
            # Add a subtle separator paragraph with reduced spacing
            sep = text_frame.add_paragraph()
            sep.text = "─" * 5 
            sz = para_styles[0]["font_obj"].size if para_styles and para_styles[0].get("font_obj") else 120000
            sep.font.size = int(sz * 0.3)
            sep.font.color.rgb = RGBColor(128, 128, 128) # Grey separator
        translated_lines = [apply_cjk_line_breaking(l.strip()) for l in translated_text.split("\n") if l.strip()]
        for index, line in enumerate(translated_lines):
            paragraph = text_frame.paragraphs[0] if index == 0 and not source_lines else text_frame.add_paragraph()
            paragraph.text = line
            style_idx = min(index, len(content_styles) - 1) if content_styles else -1
            if style_idx >= 0:
                apply_paragraph_style(paragraph, content_styles[style_idx], scale=scale, target_language=target_language, font_mapping=font_mapping)
        return True
    except Exception: return False

def set_corrected_text(text_frame: TextFrame, lines: list[str], color: RGBColor|None=None) -> bool:
    try:
        lines = [sanitize_xml_text(l) for l in lines]; para_styles = capture_full_frame_styles(text_frame)
        text_frame.clear()
        for index, line in enumerate(lines):
            paragraph = text_frame.paragraphs[0] if index == 0 else text_frame.add_paragraph()
            paragraph.text = line
            style_idx = min(index, len(para_styles) - 1) if para_styles else -1
            if style_idx >= 0: apply_paragraph_style(paragraph, para_styles[style_idx])
            if color and paragraph.runs:
                for run in paragraph.runs: run.font.color.rgb = color
        return True
    except Exception: return False
