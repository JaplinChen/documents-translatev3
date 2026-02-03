from __future__ import annotations

import logging
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.api.error_handler import api_error_handler
from backend.services.docx.extract import extract_blocks as extract_docx_blocks
from backend.services.document_cache import doc_cache
from backend.services.language_detect import detect_document_languages

LOGGER = logging.getLogger(__name__)

router = APIRouter()


@router.post("/extract")
@api_error_handler(validate_file=False, read_error_msg="DOCX 檔案無效")
async def docx_extract(
    file: UploadFile = File(...),
    refresh: bool = False,
    source_language: str | None = Form(None),
) -> dict:
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="只支援 .docx 檔案")

    docx_bytes = await file.read()
    file_hash = doc_cache.get_hash(docx_bytes)

    if not refresh:
        cached = doc_cache.get(file_hash)
        if cached:
            blocks = cached["blocks"]
            meta = cached["metadata"]
            return {
                "blocks": blocks,
                "language_summary": detect_document_languages(blocks),
                "slide_width": meta.get("slide_width"),
                "slide_height": meta.get("slide_height"),
                "cache_hit": True,
            }

    data = extract_docx_blocks(docx_bytes, preferred_lang=source_language)
    blocks = data["blocks"]
    sw = data["slide_width"]
    sh = data["slide_height"]

    doc_cache.set(
        file_hash,
        blocks,
        {"slide_width": sw, "slide_height": sh},
        "docx",
    )

    return {
        "blocks": blocks,
        "language_summary": detect_document_languages(blocks),
        "slide_width": sw,
        "slide_height": sh,
        "cache_hit": False,
    }
