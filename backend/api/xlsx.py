from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.api.error_handler import api_error_handler
from backend.api.download_utils import build_download_response
from backend.api.pptx_naming import generate_semantic_filename_with_ext
from backend.api.pptx_translate import TranslateRequest, pptx_translate_stream
from backend.api.pptx_utils import validate_file_type
from backend.services.language_detect import detect_document_languages
from backend.services.layout_registry import resolve_layout_apply_value
from backend.services.xlsx.apply import apply_bilingual, apply_translations
from backend.services.xlsx.extract import extract_blocks as extract_xlsx_blocks
from backend.services.document_cache import doc_cache

router = APIRouter(prefix="/api/xlsx")


@router.post("/extract")
@api_error_handler(read_error_msg="XLSX 檔案無效")
async def xlsx_extract(
    file: UploadFile = File(...),
    refresh: bool = False,
    source_language: str | None = Form(None),
    layout_params: str | None = Form(None),
) -> dict:
    xlsx_bytes = await file.read()

    # 解析 layout_params
    parsed_params: dict = {}
    if layout_params:
        import json
        try:
            maybe_obj = json.loads(layout_params)
            if isinstance(maybe_obj, dict):
                parsed_params = maybe_obj
        except Exception:
            pass

    # 使用檔案與參數共同作為快取鍵，確保設定變更時能正確重新抽取
    file_hash = doc_cache.get_hash(xlsx_bytes, extra_data=parsed_params)

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
        data = extract_xlsx_blocks(
            input_path,
            preferred_lang=source_language,
            layout_params=parsed_params
        )
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
    layout_id: str | None = Form(None),
    layout_params: str | None = Form(None),
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
    parsed_layout_params: dict = {}
    if layout_params:
        import json
        try:
            maybe_obj = json.loads(layout_params)
            if isinstance(maybe_obj, dict):
                parsed_layout_params = maybe_obj
        except Exception:
            parsed_layout_params = {}

    if mode not in {"bilingual", "translated"}:
        raise HTTPException(status_code=400, detail="不支援的 mode")
    apply_layout = resolve_layout_apply_value(
        layout_id=layout_id,
        file_type="xlsx",
        mode=mode,
        fallback_value=bilingual_layout,
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        in_p = os.path.join(temp_dir, "in.xlsx")
        out_p = os.path.join(temp_dir, "out.xlsx")
        with open(in_p, "wb") as h:
            h.write(xlsx_bytes)

        if mode == "bilingual":
            apply_bilingual(
                in_p,
                out_p,
                blocks_data,
                layout=apply_layout,
                layout_params=parsed_layout_params,
            )
        else:
            apply_translations(in_p, out_p, blocks_data)

        with open(out_p, "rb") as h:
            output_bytes = h.read()

    final_filename = generate_semantic_filename_with_ext(
        file.filename,
        mode,
        apply_layout,
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
    return build_download_response(
        filename,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.post("/translate-stream")
async def xlsx_translate_stream(
    request: TranslateRequest,
):
    """Reuse the core PPTX streaming translation logic for XLSX."""
    return await pptx_translate_stream(request)
