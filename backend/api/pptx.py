"""PPTX API endpoints.

This module provides REST API endpoints for PPTX file extraction,
application of translated content, and language detection.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import uuid
import time
import re
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse

LOGGER = logging.getLogger(__name__)

from backend.api.pptx_utils import validate_file_type
from backend.contracts import coerce_blocks
from backend.services.language_detect import detect_document_languages
from backend.services.pptx.apply import apply_bilingual, apply_chinese_corrections, apply_translations
from backend.services.pptx.extract import extract_blocks as extract_pptx_blocks
from backend.api.pptx_naming import generate_semantic_filename
from backend.api.pptx_history import get_history_items, delete_history_file

router = APIRouter(prefix="/api/pptx")

@router.post("/extract")
async def pptx_extract(file: UploadFile = File(...)) -> dict:
    valid, err = validate_file_type(file.filename)
    if not valid: raise HTTPException(status_code=400, detail=err)
    try: pptx_bytes = await file.read()
    except Exception as exc: raise HTTPException(status_code=400, detail="PPTX 檔案無效") from exc

    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, "input.pptx")
        with open(input_path, "wb") as h: h.write(pptx_bytes)
        data = extract_pptx_blocks(input_path)
        blocks, sw, sh = data["blocks"], data["slide_width"], data["slide_height"]

    return {"blocks": blocks, "language_summary": detect_document_languages(blocks), "slide_width": sw, "slide_height": sh}

@router.post("/languages")
async def pptx_languages(file: UploadFile = File(...)) -> dict:
    valid, err = validate_file_type(file.filename)
    if not valid: raise HTTPException(status_code=400, detail=err)
    try: pptx_bytes = await file.read()
    except Exception as exc: raise HTTPException(status_code=400, detail="PPTX 檔案無效") from exc

    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, "input.pptx")
        with open(input_path, "wb") as h: h.write(pptx_bytes)
        blocks = extract_pptx_blocks(input_path)["blocks"]
    return {"language_summary": detect_document_languages(blocks)}

@router.post("/apply")
async def pptx_apply(
    file: UploadFile = File(...), blocks: str = Form(...), mode: str = Form("bilingual"),
    bilingual_layout: str = Form("inline"), fill_color: str|None = Form(None),
    text_color: str|None = Form(None), line_color: str|None = Form(None),
    line_dash: str|None = Form(None), font_mapping: str|None = Form(None),
    target_language: str|None = Form(None),
) -> dict:
    valid, err = validate_file_type(file.filename)
    if not valid: raise HTTPException(status_code=400, detail=err)
    try: pptx_bytes = await file.read()
    except Exception as exc: raise HTTPException(status_code=400, detail="PPTX 檔案無效") from exc

    try:
        blocks_data = coerce_blocks(json.loads(blocks))
        parsed_font_mapping = json.loads(font_mapping) if font_mapping else None
    except Exception as exc: raise HTTPException(status_code=400, detail="資料格式錯誤") from exc

    if mode not in {"bilingual", "correction", "translated"}: raise HTTPException(status_code=400, detail="不支援的 mode")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        in_p, out_p = os.path.join(temp_dir, "in.pptx"), os.path.join(temp_dir, "out.pptx")
        with open(in_p, "wb") as h: h.write(pptx_bytes)

        if mode == "bilingual":
            apply_bilingual(in_p, out_p, blocks_data, layout=bilingual_layout, target_language=target_language, font_mapping=parsed_font_mapping)
        elif mode == "translated":
            apply_translations(in_p, out_p, blocks_data, mode="direct", target_language=target_language, font_mapping=parsed_font_mapping)
        else:
            apply_chinese_corrections(in_p, out_p, blocks_data, fill_color=fill_color, text_color=text_color, line_color=line_color, line_dash=line_dash)

        with open(out_p, "rb") as h: output_bytes = h.read()

    final_filename = generate_semantic_filename(file.filename, mode, bilingual_layout)
    save_path = Path("data/exports") / final_filename
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "wb") as f: f.write(output_bytes)
        
    import urllib.parse
    safe_uri = urllib.parse.quote(final_filename, safe='')
    return {"status": "success", "filename": final_filename, "download_url": f"/api/pptx/download/{safe_uri}", "version": "20260122-REFACTORED"}

@router.get("/download/{filename:path}")
async def pptx_download(filename: str):
    import urllib.parse
    if "%" in filename: filename = urllib.parse.unquote(filename)
    file_path = Path("data/exports") / filename
    if not file_path.exists(): raise HTTPException(status_code=404, detail="檔案不存在")
        
    ascii_name = "".join(c if ord(c) < 128 else "_" for c in filename)
    safe_name = urllib.parse.quote(filename, safe='')
    return FileResponse(path=file_path, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        headers={"Content-Disposition": f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{safe_name}',
                                 "Access-Control-Expose-Headers": "Content-Disposition", "Cache-Control": "no-cache"})

@router.post("/extract-glossary")
async def pptx_extract_glossary(
    blocks: str = Form(...), target_language: str = Form("zh-TW"), provider: str|None = Form(None),
    model: str|None = Form(None), api_key: str|None = Form(None), base_url: str|None = Form(None),
) -> dict:
    from backend.services.glossary_extraction import extract_glossary_terms
    try: blocks_data = json.loads(blocks)
    except Exception as exc: raise HTTPException(status_code=418, detail="blocks JSON 無效") from exc
    try:
        terms = extract_glossary_terms(blocks_data, target_language, provider=provider, model=model, api_key=api_key, base_url=base_url)
        return {"terms": terms}
    except Exception as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.get("/debug-version")
async def pptx_debug_version(): return {"version": "20260122-REFACTORED"}

@router.get("/history")
async def pptx_history() -> dict: return {"items": get_history_items()}

@router.delete("/history/{filename:path}")
async def pptx_delete_history(filename: str):
    import urllib.parse
    if "%" in filename: filename = urllib.parse.unquote(filename)
    if delete_history_file(filename): return {"status": "success", "message": "File deleted"}
    raise HTTPException(status_code=404, detail="File not found")
