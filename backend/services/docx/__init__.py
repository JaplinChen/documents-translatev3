"""
DOCX Services Module - Word document processing.
"""
from .apply import apply_translations, apply_bilingual, apply_chinese_corrections
from .extract import extract_blocks

__all__ = [
    "apply_translations",
    "apply_bilingual",
    "apply_chinese_corrections",
    "extract_blocks",
]
