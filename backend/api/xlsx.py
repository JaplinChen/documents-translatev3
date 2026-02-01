from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from backend.api.error_handler import api_error_handler, validate_json_blocks
from backend.api.pptx_naming import generate_semantic_filename_with_ext
from backend.api.pptx_translate import TranslateRequest, pptx_translate_stream
from backend.api.pptx_utils import validate_file_type
from backend.services.language_detect import detect_document_languages
from backend.services.xlsx.apply import apply_bilingual, apply_translations
from backend.services.xlsx.extract import extract_blocks as extract_xlsx_blocks
from backend.services.document_cache import doc_cache

router = APIRouter(prefix="/api/xlsx")


@router.post("/extract")
@api_error_handler(read_error_msg="XLSX 檔案無效")
async def xlsx_extract(
    file: UploadFile = File(...),
    refresh: bool = False,
) -> dict:
    xlsx_bytes = await file.read()
    file_hash = doc_cache.get_hash(xlsx_bytes)

    if not refresh:
        cached = doc_cache.get(file_hash)
        if cached:
            blocks = cached["blocks"]
            meta = cached["metadata"]
            return {
                "blocks": blocks,
                "language_summary": detect_document_languages(blocks),
                "sheet_count": meta.get("sheet_count", 0),
                "cache_hit": True,
            }

    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, "input.xlsx")
        with open(input_path, "wb") as h:
            h.write(xlsx_bytes)
        data = extract_xlsx_blocks(input_path)
        blocks = data["blocks"]
        sheet_count = data.get("sheet_count", 0)

    # 更新快取
    doc_cache.set(file_hash, blocks, {"sheet_count": sheet_count}, "xlsx")

    return {
        "blocks": blocks,
        "language_summary": detect_document_languages(blocks),
        "sheet_count": sheet_count,
        "cache_hit": False,
    }


@router.post("/apply")
@api_error_handler(validate_file=False)  # Manual validation for complex params
async def xlsx_apply(
    file: UploadFile = File(...),
    blocks: str = Form(...),
    mode: str = Form("bilingual"),
    bilingual_layout: str = Form("inline"),
    target_language: str | None = Form(None),
) -> dict:
    # Manual file validation
    valid, err = validate_file_type(file.filename)
    if not valid:
        raise HTTPException(status_code=400, detail=err)

    xlsx_bytes = await file.read()  # File read handled by decorator

    # Parse and validate JSON data
    from backend.api.error_handler import parse_json_blocks

    blocks_data = parse_json_blocks(blocks)

    if mode not in {"bilingual", "translated"}:
        raise HTTPException(status_code=400, detail="不支援的 mode")

    with tempfile.TemporaryDirectory() as temp_dir:
        in_p = os.path.join(temp_dir, "in.xlsx")
        out_p = os.path.join(temp_dir, "out.xlsx")
        with open(in_p, "wb") as h:
            h.write(xlsx_bytes)

        if mode == "bilingual":
            apply_bilingual(in_p, out_p, blocks_data, layout=bilingual_layout)
        else:
            apply_translations(in_p, out_p, blocks_data)

        with open(out_p, "rb") as h:
            output_bytes = h.read()

    final_filename = generate_semantic_filename_with_ext(
        file.filename,
        mode,
        bilingual_layout,
        ".xlsx",
    )
    save_path = Path("data/exports") / final_filename
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(output_bytes)

    import urllib.parse

    safe_uri = urllib.parse.quote(final_filename, safe="")
    return {
        "status": "success",
        "filename": final_filename,
        "download_url": f"/api/xlsx/download/{safe_uri}",
    }


@router.get("/download/{filename:path}")
async def xlsx_download(filename: str):
    import urllib.parse

    # Resolve the path relative to exports
    file_path = Path("data/exports") / filename
    if not file_path.exists():
        # Fallback to unquoted name
        alt_path = Path("data/exports") / urllib.parse.unquote(filename)
        if alt_path.exists():
            file_path = alt_path
        else:
            raise HTTPException(status_code=404, detail="檔案不存在")

    actual_filename = file_path.name
    ascii_name = "".join(c if ord(c) < 128 else "_" for c in actual_filename)
    safe_name = urllib.parse.quote(actual_filename, safe="")
    disposition = f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{safe_name}"

    return FileResponse(
        path=file_path,
        media_type=("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        headers={
            "Content-Disposition": disposition,
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Cache-Control": "no-cache",
        },
    )


@router.post("/translate-stream")
async def xlsx_translate_stream(
    request: TranslateRequest,
):
    """Reuse the core PPTX streaming translation logic for XLSX."""
    return await pptx_translate_stream(request)
