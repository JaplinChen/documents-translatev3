from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from backend.api.pptx_utils import validate_file_type
from backend.services.language_detect import detect_document_languages
from backend.services.pdf.extract import extract_blocks as extract_pdf_blocks
from backend.api.pptx_naming import generate_semantic_filename

router = APIRouter(prefix="/api/pdf")

@router.post("/extract")
async def pdf_extract(file: UploadFile = File(...)) -> dict:
    valid, err = validate_file_type(file.filename)
    if not valid: raise HTTPException(status_code=400, detail=err)
    try: pdf_bytes = await file.read()
    except Exception as exc: raise HTTPException(status_code=400, detail="PDF 檔案無效") from exc

    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, "input.pdf")
        with open(input_path, "wb") as h: h.write(pdf_bytes)
        data = extract_pdf_blocks(input_path)
        blocks = data["blocks"]

    return {
        "blocks": blocks, 
        "language_summary": detect_document_languages(blocks),
        "page_count": data.get("page_count", 0)
    }

@router.post("/apply")
async def pdf_apply(
    file: UploadFile = File(...), 
    blocks: str = Form(...), 
    mode: str = Form("bilingual"),
) -> dict:
    # PDF Apply logic is complex. For POC, we might return a text-based comparison or a simple reconstruction.
    # For now, we return a 501 Not Implemented specifically for PDF Apply
    raise HTTPException(status_code=501, detail="PDF 翻譯回寫功能尚在開發中，目前僅支援文字擷取與預覽。")
