"""PPTX API endpoints.

This module provides REST API endpoints for PPTX file extraction,
application of translated content, and language detection.
"""

from __future__ import annotations

import json
import os
import tempfile
import urllib.parse
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from backend.api.error_handler import api_error_handler, validate_json_blocks
from backend.api.pptx_history import delete_history_file, get_history_items
from backend.api.pptx_naming import generate_semantic_filename
from backend.api.pptx_utils import validate_file_type
from backend.services.language_detect import detect_document_languages
from backend.services.pptx.apply import (
    apply_bilingual,
    apply_chinese_corrections,
    apply_translations,
)
from backend.services.pptx.extract import extract_blocks as extract_pptx_blocks
from backend.services.document_cache import doc_cache
from backend.services.thumbnail_service import generate_pptx_thumbnails

router = APIRouter(prefix="/api/pptx")


@router.post("/extract")
@api_error_handler(read_error_msg="PPTX 檔案無效")
async def pptx_extract(
    file: UploadFile = File(...),
    refresh: bool = False,
) -> dict:
    pptx_bytes = await file.read()
    file_hash = doc_cache.get_hash(pptx_bytes)

    if not refresh:
        cached = doc_cache.get(file_hash)
        if cached:
            blocks = cached["blocks"]
            meta = cached["metadata"]
            thumbs = meta.get("thumbnail_urls", [])

            # Check if thumbnails actually exist on disk
            thumbnails_ok = False
            if thumbs and len(thumbs) > 0:
                # Check the first thumbnail
                # Convert URL "/thumbnails/hash_0.png" to path "data/thumbnails/hash_0.png"
                # Handle potential legacy URLs (e.g., missing prefix or absolute path confusion)
                first_url = thumbs[0]
                filename = first_url.split("/")[-1]
                if (Path("data/thumbnails") / filename).exists():
                    thumbnails_ok = True

            if not thumbnails_ok:
                # Regenerate thumbnails if missing
                with tempfile.TemporaryDirectory() as temp_dir:
                    input_path = os.path.join(temp_dir, "input.pptx")
                    with open(input_path, "wb") as h:
                        h.write(pptx_bytes)
                    thumbs = generate_pptx_thumbnails(input_path)
                    # Update cache with new valid URLs
                    doc_cache.update_metadata(file_hash, {"thumbnail_urls": thumbs})

            return {
                "blocks": blocks,
                "language_summary": detect_document_languages(blocks),
                "slide_width": meta.get("slide_width"),
                "slide_height": meta.get("slide_height"),
                "thumbnail_urls": thumbs,
                "cache_hit": True,
            }

    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, "input.pptx")
        with open(input_path, "wb") as h:
            h.write(pptx_bytes)
        data = extract_pptx_blocks(input_path)
        blocks = data["blocks"]
        sw = data["slide_width"]
        sh = data["slide_height"]

        # Generate high-fidelity thumbnails
        thumbs = generate_pptx_thumbnails(input_path)

    # 更新快取
    doc_cache.set(
        file_hash,
        blocks,
        {"slide_width": sw, "slide_height": sh, "thumbnail_urls": thumbs},
        "pptx",
    )

    return {
        "blocks": blocks,
        "language_summary": detect_document_languages(blocks),
        "slide_width": sw,
        "slide_height": sh,
        "thumbnail_urls": thumbs,
        "cache_hit": False,
    }


@router.post("/languages")
@api_error_handler(read_error_msg="PPTX 檔案無效")
async def pptx_languages(file: UploadFile = File(...)) -> dict:
    pptx_bytes = await file.read()  # File validation handled by decorator

    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, "input.pptx")
        with open(input_path, "wb") as h:
            h.write(pptx_bytes)
        blocks = extract_pptx_blocks(input_path)["blocks"]
    return {"language_summary": detect_document_languages(blocks)}


@router.post("/apply")
@api_error_handler(validate_file=False)  # Manual validation for complex params
async def pptx_apply(
    file: UploadFile = File(...),
    blocks: str = Form(...),
    mode: str = Form("bilingual"),
    bilingual_layout: str = Form("inline"),
    fill_color: str | None = Form(None),
    text_color: str | None = Form(None),
    line_color: str | None = Form(None),
    line_dash: str | None = Form(None),
    font_mapping: str | None = Form(None),
    target_language: str | None = Form(None),
) -> dict:
    # Manual file validation
    valid, err = validate_file_type(file.filename)
    if not valid:
        raise HTTPException(status_code=400, detail=err)

    pptx_bytes = await file.read()  # File read handled by decorator

    # Parse and validate JSON data
    blocks_data = validate_json_blocks(blocks)
    parsed_font_mapping = json.loads(font_mapping) if font_mapping else None

    if mode not in {"bilingual", "correction", "translated"}:
        raise HTTPException(status_code=400, detail="不支援的 mode")

    with tempfile.TemporaryDirectory() as temp_dir:
        in_p = os.path.join(temp_dir, "in.pptx")
        out_p = os.path.join(temp_dir, "out.pptx")
        with open(in_p, "wb") as h:
            h.write(pptx_bytes)

        if mode == "bilingual":
            apply_bilingual(
                in_p,
                out_p,
                blocks_data,
                layout=bilingual_layout,
                target_language=target_language,
                font_mapping=parsed_font_mapping,
            )
        elif mode == "translated":
            apply_translations(
                in_p,
                out_p,
                blocks_data,
                mode="direct",
                target_language=target_language,
                font_mapping=parsed_font_mapping,
            )
        else:
            apply_chinese_corrections(
                in_p,
                out_p,
                blocks_data,
                fill_color=fill_color,
                text_color=text_color,
                line_color=line_color,
                line_dash=line_dash,
            )

        with open(out_p, "rb") as h:
            output_bytes = h.read()

    final_filename = generate_semantic_filename(
        file.filename,
        mode,
        bilingual_layout,
    )
    save_path = Path("data/exports") / final_filename
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(output_bytes)

    safe_uri = urllib.parse.quote(final_filename, safe="")
    return {
        "status": "success",
        "filename": final_filename,
        "download_url": f"/api/pptx/download/{safe_uri}",
        "version": "20260122-REFACTORED",
    }


@router.get("/download/{filename:path}")
async def pptx_download(filename: str):
    # Resolve the path relative to exports
    file_path = Path("data/exports") / filename
    if not file_path.exists():
        # Fallback to unquoted name if necessary (sometimes URL routing decodes automatically)
        alt_path = Path("data/exports") / urllib.parse.unquote(filename)
        if alt_path.exists():
            file_path = alt_path
        else:
            raise HTTPException(status_code=404, detail="檔案不存在")

    actual_filename = file_path.name
    ascii_name = "".join(c if ord(c) < 128 else "_" for c in actual_filename)
    safe_name = urllib.parse.quote(actual_filename, safe="")

    # Modern RFC 5987 compliant header
    content_disposition = f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{safe_name}"

    media_type = (
        "application/json"
        if file_path.suffix.lower() == ".json"
        else "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    return FileResponse(
        path=file_path,
        media_type=media_type,
        headers={
            "Content-Disposition": content_disposition,
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Cache-Control": "no-cache",
        },
    )


@router.get("/debug-version")
async def pptx_debug_version():
    return {"version": "20260122-REFACTORED"}


@router.get("/history")
async def pptx_history() -> dict:
    return {"items": get_history_items()}


@router.delete("/history/{filename:path}")
async def pptx_delete_history(filename: str):
    import urllib.parse

    if "%" in filename:
        filename = urllib.parse.unquote(filename)
    if delete_history_file(filename):
        return {"status": "success", "message": "File deleted"}
    raise HTTPException(status_code=404, detail="File not found")
