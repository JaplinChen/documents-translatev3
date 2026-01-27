"""PPTX Services Module - PowerPoint document processing."""
# Apply functions
from .apply import (
    apply_bilingual,
    apply_chinese_corrections,
    apply_translations,
)
from .apply_core import _apply_translations_to_presentation
from .apply_layout import add_overflow_textboxes, capture_font_spec, fix_title_overlap
from .apply_shape import (
    _iter_shapes,
    find_shape_in_shapes,
    find_shape_with_id,
    iter_table_cells,
)
from .apply_slide import duplicate_slide, insert_slide_after
from .apply_text import (
    apply_shape_highlight,
    build_corrected_lines,
    set_bilingual_text,
    set_corrected_text,
    set_text_preserve_format,
)

# Extract functions
from .extract import extract_blocks
from .text_styles import (
    apply_paragraph_style,
    capture_full_frame_styles,
)

# Text utilities
from .text_utils import parse_hex_color, sanitize_xml_text, split_text_chunks

# XML utilities
from .xml_core import get_pptx_theme_summary

__all__ = [
    # Apply
    "apply_translations",
    "apply_bilingual",
    "apply_chinese_corrections",
    "_apply_translations_to_presentation",
    "capture_font_spec",
    "add_overflow_textboxes",
    "fix_title_overlap",
    "_iter_shapes",
    "find_shape_in_shapes",
    "find_shape_with_id",
    "iter_table_cells",
    "duplicate_slide",
    "insert_slide_after",
    "apply_shape_highlight",
    "set_text_preserve_format",
    "set_bilingual_text",
    "set_corrected_text",
    "build_corrected_lines",
    # Extract
    "extract_blocks",
    # Text
    "sanitize_xml_text",
    "parse_hex_color",
    "split_text_chunks",
    "capture_full_frame_styles",
    "apply_paragraph_style",
    # XML
    "get_pptx_theme_summary",
]
