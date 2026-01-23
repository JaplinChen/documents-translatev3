from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from backend.api.pptx_utils import validate_file_type
from backend.contracts import coerce_blocks
from backend.services.language_detect import detect_document_languages
from backend.services.xlsx.apply import apply_bilingual, apply_translations
from backend.services.xlsx.extract import extract_blocks as extract_xlsx_blocks
from backend.api.pptx_naming import generate_semantic_filename

router = APIRouter(prefix="/api/xlsx")

@router.post("/extract")
async def xlsx_extract(file: UploadFile = File(...)) -> dict:
    valid, err = validate_file_type(file.filename)
    if not valid: raise HTTPException(status_code=400, detail=err)
    try: xlsx_bytes = await file.read()
    except Exception as exc: raise HTTPException(status_code=400, detail="XLSX 檔案無效") from exc

    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, "input.xlsx")
        with open(input_path, "wb") as h: h.write(xlsx_bytes)
        data = extract_xlsx_blocks(input_path)
        blocks = data["blocks"]

    return {
        "blocks": blocks, 
        "language_summary": detect_document_languages(blocks),
        "sheet_count": data.get("sheet_count", 0)
    }

@router.post("/apply")
async def xlsx_apply(
    file: UploadFile = File(...), 
    blocks: str = Form(...), 
    mode: str = Form("bilingual"),
    bilingual_layout: str = Form("inline"),
    target_language: str|None = Form(None),
) -> dict:
    valid, err = validate_file_type(file.filename)
    if not valid: raise HTTPException(status_code=400, detail=err)
    try: xlsx_bytes = await file.read()
    except Exception as exc: raise HTTPException(status_code=400, detail="XLSX 檔案無效") from exc

    try:
        blocks_data = coerce_blocks(json.loads(blocks))
    except Exception as exc: raise HTTPException(status_code=400, detail="資料格式錯誤") from exc

    if mode not in {"bilingual", "translated"}: raise HTTPException(status_code=400, detail="不支援的 mode")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        in_p, out_p = os.path.join(temp_dir, "in.xlsx"), os.path.join(temp_dir, "out.xlsx")
        with open(in_p, "wb") as h: h.write(xlsx_bytes)

        if mode == "bilingual":
            apply_bilingual(in_p, out_p, blocks_data, layout=bilingual_layout)
        else:
            apply_translations(in_p, out_p, blocks_data)

        with open(out_p, "rb") as h: output_bytes = h.read()

    final_filename = generate_semantic_filename(file.filename, mode, bilingual_layout)
    save_path = Path("data/exports") / final_filename
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "wb") as f: f.write(output_bytes)
        
    import urllib.parse
    safe_uri = urllib.parse.quote(final_filename, safe='')
    return {
        "status": "success", 
        "filename": final_filename, 
        "download_url": f"/api/xlsx/download/{safe_uri}"
    }

@router.get("/download/{filename:path}")
async def xlsx_download(filename: str):
    import urllib.parse
    if "%" in filename: filename = urllib.parse.unquote(filename)
    file_path = Path("data/exports") / filename
    if not file_path.exists(): raise HTTPException(status_code=404, detail="檔案不存在")
        
    ascii_name = "".join(c if ord(c) < 128 else "_" for c in filename)
    safe_name = urllib.parse.quote(filename, safe='')
    return FileResponse(
        path=file_path, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{safe_name}',
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Cache-Control": "no-cache"
        }
    )
