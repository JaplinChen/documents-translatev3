from __future__ import annotations

from io import BytesIO
import zipfile

from docx import Document

from backend.contracts import make_block
from backend.services.extract_utils import (
    is_exact_term_match,
    is_garbage_text,
    is_numeric_only,
    is_technical_terms_only,
    sanitize_extracted_text,
)
from backend.services.image_ocr import extract_image_text_blocks
from backend.services.language_detect import detect_document_languages
from backend.services.ocr_lang import resolve_ocr_lang_from_doc_lang


def extract_blocks(docx_path: str | bytes, preferred_lang: str | None = None) -> dict:
    """Extract text blocks from a .docx file."""
    if isinstance(docx_path, bytes):
        doc = Document(BytesIO(docx_path))
    else:
        doc = Document(docx_path)

    blocks: list[dict] = []

    # 1. Extract Paragraphs
    for i, para in enumerate(doc.paragraphs):
        text = sanitize_extracted_text(para.text)
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
                text = sanitize_extracted_text(cell.text)
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

    doc_lang = preferred_lang or (detect_document_languages(blocks).get("primary") if blocks else None)
    ocr_lang = resolve_ocr_lang_from_doc_lang(doc_lang)

    # 3. Extract Images (inline shapes)
    for idx, shape in enumerate(doc.inline_shapes):
        try:
            r_id = shape._inline.graphic.graphicData.pic.blipFill.blip.embed  # noqa: SLF001
            part = doc.part.related_parts.get(r_id)
            if not part:
                continue
            image_part = str(part.partname)
            image_bytes = part.blob
            blocks.extend(
                extract_image_text_blocks(
                    image_bytes,
                    slide_index=-1,
                    shape_id=f"docx-image-{idx}",
                    image_part=image_part,
                    source="docx",
                    ocr_lang=ocr_lang,
                )
            )
        except Exception:
            continue

    # 4. Fallback: scan media parts directly
    try:
        if isinstance(docx_path, (str, bytes)):
            docx_fs_path = docx_path if isinstance(docx_path, str) else None
            if docx_fs_path:
                with zipfile.ZipFile(docx_fs_path, "r") as zf:
                    media_files = [n for n in zf.namelist() if n.startswith("word/media/")]
                    for idx, name in enumerate(media_files):
                        try:
                            image_bytes = zf.read(name)
                        except Exception:
                            continue
                        blocks.extend(
                            extract_image_text_blocks(
                                image_bytes,
                                slide_index=-1,
                                shape_id=f"docx-media-{idx}",
                                image_part=name,
                                source="docx",
                                ocr_lang=ocr_lang,
                            )
                        )
    except Exception:
        pass

    return {
        "blocks": blocks,
        "slide_width": 595,  # A4 width in points approx
        "slide_height": 842,  # A4 height in points approx
    }
