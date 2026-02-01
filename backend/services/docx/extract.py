from __future__ import annotations

from io import BytesIO

from docx import Document

from backend.contracts import make_block
from backend.services.extract_utils import (
    is_exact_term_match,
    is_garbage_text,
    is_numeric_only,
    is_technical_terms_only,
)


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
        if (
            not text
            or is_numeric_only(text)
            or is_exact_term_match(text)
            or is_technical_terms_only(text)
            or is_garbage_text(text)
        ):
            continue
        # Note: slide_index is used as paragraph_index for UI expectations.
        # Use 'textbox' as 'paragraph' is not in PPTXBlock Literal
        blocks.append(make_block(i, i, "textbox", text, x=0, y=0, width=500, height=20))

    # 2. Extract Tables
    for t_idx, table in enumerate(doc.tables):
        for r_idx, row in enumerate(table.rows):
            for c_idx, cell in enumerate(row.cells):
                text = cell.text.strip()
                if (
                    not text
                    or is_numeric_only(text)
                    or is_exact_term_match(text)
                    or is_technical_terms_only(text)
                    or is_garbage_text(text)
                ):
                    continue
                # Unique integer ID:
                # table_idx * 1000 + row_idx * 100 + cell_idx
                shape_id = t_idx * 1000 + r_idx * 100 + c_idx
                blocks.append(
                    make_block(
                        t_idx,
                        shape_id,
                        "table_cell",
                        text,
                        x=0,
                        y=0,
                        width=500,
                        height=50,
                    )
                )

    return {
        "blocks": blocks,
        "slide_width": 595,  # A4 width in points approx
        "slide_height": 842,  # A4 height in points approx
    }
