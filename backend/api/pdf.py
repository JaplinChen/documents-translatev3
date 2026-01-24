import json
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from backend.api.pptx_naming import generate_semantic_filename_with_ext
from backend.api.pptx_translate import pptx_translate_stream
from backend.api.pptx_utils import validate_file_type
from backend.contracts import coerce_blocks
from backend.services.language_detect import detect_document_languages
from backend.services.pdf.apply import apply_bilingual, apply_translations
from backend.services.pdf.extract import extract_blocks as extract_pdf_blocks

router = APIRouter(prefix="/api/pdf")

@router.post("/extract")
async def pdf_extract(file: UploadFile = File(...)) -> dict:
    valid, err = validate_file_type(file.filename)
    if not valid:
        raise HTTPException(status_code=400, detail=err)

    try:
        pdf_bytes = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="PDF 檔案無效") from exc

    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, "input.pdf")
        with open(input_path, "wb") as h:
            h.write(pdf_bytes)
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

    if mode not in {"bilingual", "translated"}:
        raise HTTPException(status_code=400, detail="不支援的 mode")

    with tempfile.TemporaryDirectory() as temp_dir:
        in_p = os.path.join(temp_dir, "in.pdf")
        out_p = os.path.join(temp_dir, "out.pdf")
        with open(in_p, "wb") as h:
            h.write(pdf_bytes)

        if mode == "bilingual":
            apply_bilingual(in_p, out_p, blocks_data)
        else:
            apply_translations(in_p, out_p, blocks_data)

        with open(out_p, "rb") as h:
            output_bytes = h.read()

    final_filename = generate_semantic_filename_with_ext(
        file.filename,
        mode,
        "inline",
        ".pdf",
    )
    save_path = Path("data/exports") / final_filename
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(output_bytes)

    import urllib.parse
    safe_uri = urllib.parse.quote(final_filename, safe='')
    return {
        "status": "success",
        "filename": final_filename,
        "download_url": f"/api/pdf/download/{safe_uri}"
    }

@router.get("/download/{filename:path}")
async def pdf_download(filename: str):
    import urllib.parse
    if "%" in filename:
        filename = urllib.parse.unquote(filename)
    file_path = Path("data/exports") / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="檔案不存在")

    ascii_name = "".join(c if ord(c) < 128 else "_" for c in filename)
    safe_name = urllib.parse.quote(filename, safe='')
    disposition = f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{safe_name}'
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        headers={
            "Content-Disposition": disposition,
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Cache-Control": "no-cache"
        }
    )

@router.post("/translate-stream")
async def pdf_translate_stream(
    blocks: str = Form(...),
    source_language: str | None = Form(None),
    target_language: str | None = Form(None),
    mode: str = Form("bilingual"),
    use_tm: bool = Form(False),
    provider: str | None = Form(None),
    model: str | None = Form(None),
    api_key: str | None = Form(None),
    base_url: str | None = Form(None),
    ollama_fast_mode: bool = Form(False),
    tone: str | None = Form(None),
    vision_context: bool = Form(True),
    smart_layout: bool = Form(True),
    refresh: bool = Form(False),
    completed_ids: str | None = Form(None),
    similarity_threshold: float = Form(0.75),
):
    """Reuse the core PPTX streaming translation logic for PDF."""
    return await pptx_translate_stream(
        blocks=blocks,
        source_language=source_language,
        target_language=target_language,
        mode=mode,
        use_tm=use_tm,
        provider=provider,
        model=model,
        api_key=api_key,
        base_url=base_url,
        ollama_fast_mode=ollama_fast_mode,
        tone=tone,
        vision_context=vision_context,
        smart_layout=smart_layout,
        refresh=refresh,
        completed_ids=completed_ids,
        similarity_threshold=similarity_threshold,
    )
