"""
PPTX Services Module - PowerPoint document processing.
"""
# Apply functions
from .apply import apply_bilingual, apply_chinese_corrections, apply_translations
from .apply_core import _apply_translations_to_presentation
from .apply_layout import (
    capture_font_spec,
    add_overflow_textboxes,
    fix_title_overlap,
    _iter_shapes,
    find_shape_in_shapes,
    find_shape_with_id,
    iter_table_cells,
    duplicate_slide,
    insert_slide_after,
)
from .apply_text import (
    apply_shape_highlight,
    set_text_preserve_format,
    set_bilingual_text,
    set_corrected_text,
    build_corrected_lines,
)

# Extract functions
from .extract import extract_blocks

# Text utilities  
from .text_utils import (
    sanitize_xml_text,
    parse_hex_color,
    split_text_chunks,
)
from .text_styles import (
    capture_full_frame_styles,
    apply_paragraph_style,
)

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
