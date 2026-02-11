import json
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Body

from backend.api.error_handler import api_error_handler
from backend.api.download_utils import build_download_response
from backend.api.pptx_naming import generate_semantic_filename_with_ext
from backend.api.pptx_translate import TranslateRequest, pptx_translate_stream
from backend.api.pptx_utils import validate_file_type
from backend.contracts import coerce_blocks
from backend.services.language_detect import detect_document_languages
from backend.services.layout_registry import resolve_layout_apply_value
from backend.services.pdf.extract import extract_blocks as extract_pdf_blocks
from backend.services.document_cache import doc_cache
from backend.services.pdf.apply import apply_bilingual, apply_translations
from backend.services.thumbnail_service import generate_pdf_thumbnails

router = APIRouter(prefix="/api/pdf")


@router.post("/extract")
@api_error_handler(read_error_msg="PDF 檔案無效")
async def pdf_extract(
    file: UploadFile = File(...),
    refresh: bool = False,
    source_language: str | None = Form(None),
) -> dict:
    pdf_bytes = await file.read()
    file_hash = doc_cache.get_hash(pdf_bytes)

    if not refresh:
        cached = doc_cache.get(file_hash)
        if cached:
            meta = cached.get("metadata", {})
            return {
                "blocks": cached["blocks"],
                "language_summary": detect_document_languages(cached["blocks"]),
                "page_count": meta.get("page_count", 0),
                "slide_width": meta.get("slide_width"),
                "slide_height": meta.get("slide_height"),
                "thumbnail_urls": meta.get("thumbnail_urls", []),
                "cache_hit": True,
            }

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        input_path = os.path.join(temp_dir, "input.pdf")
        with open(input_path, "wb") as h:
            h.write(pdf_bytes)
        data = extract_pdf_blocks(input_path, preferred_lang=source_language)
        blocks = data["blocks"]
        page_count = data["page_count"]
        sw = data.get("slide_width")
        sh = data.get("slide_height")

        # Generate thumbnails for Visual Preview
        thumbs = generate_pdf_thumbnails(input_path)

    # 更新快取
    doc_cache.set(
        file_hash,
        blocks,
        {"page_count": page_count, "slide_width": sw, "slide_height": sh, "thumbnail_urls": thumbs},
        "pdf",
    )

    return {
        "blocks": blocks,
        "language_summary": detect_document_languages(blocks),
        "page_count": page_count,
        "slide_width": sw,
        "slide_height": sh,
        "thumbnail_urls": thumbs,
        "cache_hit": False,
    }


@router.post("/apply")
async def pdf_apply(
    file: UploadFile = File(...),
    blocks: str = Form(...),
    mode: str = Form("bilingual"),
    bilingual_layout: str = Form("inline"),
    layout_id: str | None = Form(None),
    layout_params: str | None = Form(None),
) -> dict:
    valid, err = validate_file_type(file.filename)
    if not valid:
        raise HTTPException(status_code=400, detail=err)

    try:
        pdf_bytes = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="PDF 檔案無效") from exc

    try:
        blocks_data = coerce_blocks(json.loads(blocks))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="資料格式錯誤") from exc
    parsed_layout_params: dict = {}
    if layout_params:
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
        file_type="pdf",
        mode=mode,
        fallback_value=bilingual_layout,
    )

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        in_p = os.path.join(temp_dir, "in.pdf")
        out_p = os.path.join(temp_dir, "out.pdf")
        with open(in_p, "wb") as h:
            h.write(pdf_bytes)

        # Extract target language from blocks content if available
        target_lang = None
        if blocks_data:
            target_lang = blocks_data[0].get("target_lang")

        if mode == "bilingual":
            apply_bilingual(
                in_p,
                out_p,
                blocks_data,
                target_language=target_lang,
                layout_params=parsed_layout_params,
            )
        else:
            apply_translations(
                in_p,
                out_p,
                blocks_data,
                target_language=target_lang,
                layout_params=parsed_layout_params,
            )

        with open(out_p, "rb") as h:
            output_bytes = h.read()

    final_filename = generate_semantic_filename_with_ext(
        file.filename,
        mode,
        apply_layout,
        ".pdf",
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
        "download_url": f"/api/pdf/download/{safe_uri}",
    }


@router.get("/download/{filename:path}")
async def pdf_download(filename: str):
    return build_download_response(filename, "application/pdf")


@router.post("/translate-stream")
async def pdf_translate_stream(
    request: TranslateRequest,
):
    """Reuse the core PPTX streaming translation logic for PDF."""
    return await pptx_translate_stream(request)
