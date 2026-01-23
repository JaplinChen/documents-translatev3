from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path
from io import BytesIO

from docx import Document
from backend.contracts import make_block

# Reuse logic from pptx_extract
def _load_preserve_terms() -> list[dict]:
    """Load preserve terms from JSON file."""
    preserve_file = Path(__file__).parent.parent / "data" / "preserve_terms.json"
    if not preserve_file.exists():
        return []
    try:
        with open(preserve_file, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

PRESERVE_TERMS = _load_preserve_terms()

def _is_numeric_only(text: str) -> bool:
    """Check if the text consists only of numbers, punctuation, or whitespace."""
    if not text.strip():
        return True
    if re.search(r"[a-zA-Z\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]", text):
        return False
    return True

def _is_technical_terms_only(text: str) -> bool:
    """Check if the text consists only of technical terms or acronyms."""
    if not text.strip():
        return True

    text_clean = text.strip()
    for term_entry in PRESERVE_TERMS:
        term = term_entry.get("term", "")
        case_sensitive = term_entry.get("case_sensitive", True)
        if case_sensitive:
            if text_clean == term: return True
        else:
            if text_clean.lower() == term.lower(): return True

    cleaned = re.sub(r"[,、，/\s]+", " ", text).strip()
    if re.search(r"[\u4e00-\u9fff\u3040-\u30ff\u0e00-\u0e7f]", cleaned):
        return False

    sentence_indicators = (
        r"\b(the|a|an|is|are|was|were|be|have|has|had|do|does|did|will|would|can|could|should|"
        r"may|might|must|please|this|that|these|those|with|from|to|in|on|at|for|of|and|or|but)\b"
    )
    if re.search(sentence_indicators, cleaned, re.IGNORECASE):
        return False

    words = cleaned.split()
    if len(words) > 10: return False
    
    is_all_caps = all(re.match(r"^[A-Z0-9_\-]+$", w) for w in words)
    is_mixed_case = all(re.match(r"^[A-Z][a-z]*[A-Z][a-zA-Z]*$", w) for w in words)
    is_title_case = all(re.match(r"^[A-Z][a-z]+$", w) for w in words)
    is_pure_lower = all(re.match(r"^[a-z]+$", w) for w in words)

    if is_all_caps or is_mixed_case: return True
    if (is_title_case or is_pure_lower) and len(words) <= 1: return True

    return False

def extract_blocks(docx_path: str | bytes) -> dict:
    """Extract text blocks from a .docx file."""
    if isinstance(docx_path, bytes):
        doc = Document(BytesIO(docx_path))
    else:
        doc = Document(docx_path)
    
    blocks: list[dict] = []
    
    # 1. Extract Paragraphs
    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if not text or _is_numeric_only(text) or _is_technical_terms_only(text):
            continue
        # Note: slide_index is used as paragraph_index here to match UI expectations
        # Use 'textbox' as 'paragraph' is not in PPTXBlock Literal
        blocks.append(make_block(i, i, "textbox", text, x=0, y=0, width=500, height=20))

    # 2. Extract Tables
    for t_idx, table in enumerate(doc.tables):
        for r_idx, row in enumerate(table.rows):
            for c_idx, cell in enumerate(row.cells):
                text = cell.text.strip()
                if not text or _is_numeric_only(text) or _is_technical_terms_only(text):
                    continue
                # Unique integer ID for table cells: table_idx * 1000 + row_idx * 100 + cell_idx
                shape_id = t_idx * 1000 + r_idx * 100 + c_idx
                blocks.append(make_block(t_idx, shape_id, "table_cell", text, x=0, y=0, width=500, height=50))

    return {
        "blocks": blocks,
        "slide_width": 595,  # A4 width in points approx
        "slide_height": 842  # A4 height in points approx
    }
