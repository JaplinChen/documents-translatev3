"""
DOCX Services Module - Word document processing.
"""
from .apply import (
    apply_bilingual,
    apply_chinese_corrections,
    apply_translations,
)
from .extract import extract_blocks

__all__ = [
    "apply_translations",
    "apply_bilingual",
    "apply_chinese_corrections",
    "extract_blocks",
]
