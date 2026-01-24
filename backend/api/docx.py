"""DOCX API endpoints.

This module provides REST API endpoints for DOCX file extraction and application.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
import asyncio
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse

from backend.contracts import coerce_blocks
from backend.services.language_detect import detect_document_languages, resolve_source_language
from backend.api.error_handler import api_error_handler, validate_json_blocks
from backend.services.correction_mode import apply_correction_mode, prepare_blocks_for_correction
from backend.services.docx.extract import extract_blocks as extract_docx_blocks
from backend.services.docx.apply import (
    apply_bilingual,
    apply_translations,
    apply_chinese_corrections,
)
from backend.services.translate_llm import translate_blocks_async
from backend.api.pptx_naming import generate_semantic_filename

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/api/docx")


@router.post("/extract")
@api_error_handler(validate_file=False, read_error_msg="DOCX 檔案無效")
async def docx_extract(file: UploadFile = File(...)) -> dict:
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="只支援 .docx 檔案")

    docx_bytes = await file.read()  # File read handled by decorator

    data = extract_docx_blocks(docx_bytes)
    blocks = data["blocks"]
    return {
        "blocks": blocks,
        "language_summary": detect_document_languages(blocks),
        "slide_width": data["slide_width"],
        "slide_height": data["slide_height"],
    }


@router.post("/apply")
@api_error_handler(validate_file=False)  # Manual validation for custom checks
async def docx_apply(
    file: UploadFile = File(...),
    blocks: str = Form(...),
    mode: str = Form("bilingual"),
    target_language: str | None = Form(None),
) -> dict:
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="只支援 .docx 檔案")

    docx_bytes = await file.read()  # File read handled by decorator

    # Parse and validate JSON data
    blocks_data = validate_json_blocks(blocks)

    if mode not in {"bilingual", "correction", "translated"}:
        raise HTTPException(status_code=400, detail="不支援的 mode")

    with tempfile.TemporaryDirectory() as temp_dir:
        out_p = os.path.join(temp_dir, "out.docx")

        if mode == "bilingual":
            apply_bilingual(docx_bytes, out_p, blocks_data, target_language=target_language)
        elif mode == "translated":
            apply_translations(
                docx_bytes, out_p, blocks_data, mode="direct", target_language=target_language
            )
        else:
            apply_chinese_corrections(docx_bytes, out_p, blocks_data)

        with open(out_p, "rb") as h:
            output_bytes = h.read()

    # Reuse semantic naming (it might need a small adjustment for .docx)
    final_filename = generate_semantic_filename(file.filename, mode, "inline")
    if not final_filename.endswith(".docx"):
        final_filename = final_filename.rsplit(".", 1)[0] + ".docx"

    save_path = Path("data/exports") / final_filename
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(output_bytes)

    import urllib.parse

    safe_uri = urllib.parse.quote(final_filename, safe="")
    return {
        "status": "success",
        "filename": final_filename,
        "download_url": f"/api/docx/download/{safe_uri}",
    }


@router.get("/download/{filename:path}")
async def docx_download(filename: str):
    import urllib.parse

    if "%" in filename:
        filename = urllib.parse.unquote(filename)
    file_path = Path("data/exports") / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="檔案不存在")

    ascii_name = "".join(c if ord(c) < 128 else "_" for c in filename)
    safe_name = urllib.parse.quote(filename, safe="")
    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{safe_name}",
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Cache-Control": "no-cache",
        },
    )


@router.post("/translate-stream")
async def docx_translate_stream(
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
) -> StreamingResponse:
    """Translate text blocks and stream progress via SSE."""
    try:
        blocks_data = coerce_blocks(json.loads(blocks))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="blocks 資料無效") from exc

    if not target_language:
        raise HTTPException(status_code=400, detail="target_language 為必填")

    resolved_source_language = resolve_source_language(blocks_data, source_language)
    param_overrides = {"refresh": refresh}

    # 解析已完成的 ID 列表
    completed_id_set = set()
    if completed_ids:
        try:
            completed_id_set = set(json.loads(completed_ids))
        except (json.JSONDecodeError, TypeError):
            pass

    # 執行過濾
    effective_blocks = []
    for b in blocks_data:
        if not refresh and b.get("client_id") in completed_id_set:
            continue
        effective_blocks.append(b)

    def _prepare_blocks_for_correction(items: list[dict], target_lang: str | None) -> list[dict]:
        return prepare_blocks_for_correction(items, target_lang)

    async def event_generator():
        queue = asyncio.Queue()

        async def progress_cb(progress_data):
            await queue.put({"event": "progress", "data": json.dumps(progress_data)})

        try:
            # yield initial progress
            yield f"event: progress\ndata: {json.dumps({'chunk_index': 0, 'completed_indices': [], 'chunk_size': 0, 'total_pending': len(blocks_data), 'timestamp': 0})}\n\n"

            task = asyncio.create_task(
                translate_blocks_async(
                    _prepare_blocks_for_correction(effective_blocks, target_language)
                    if mode == "correction"
                    else effective_blocks,
                    target_language,
                    source_language=resolved_source_language,
                    use_tm=use_tm,
                    provider=provider,
                    model=model,
                    api_key=api_key,
                    base_url=base_url,
                    tone=tone,
                    vision_context=vision_context,
                    smart_layout=smart_layout,
                    param_overrides=param_overrides,
                    on_progress=progress_cb,
                )
            )

            while True:
                get_queue_task = asyncio.create_task(queue.get())
                done, pending = await asyncio.wait(
                    [get_queue_task, task], return_when=asyncio.FIRST_COMPLETED
                )

                if get_queue_task in done:
                    event = get_queue_task.result()
                    yield f"event: {event['event']}\ndata: {event['data']}\n\n"
                else:
                    get_queue_task.cancel()

                if task in done:
                    while not queue.empty():
                        event = queue.get_nowait()
                        yield f"event: {event['event']}\ndata: {event['data']}\n\n"
                    result = await task
                    if mode == "correction":
                        translated_texts = [
                            b.get("translated_text", "") for b in result.get("blocks", [])
                        ]
                        result["blocks"] = apply_correction_mode(
                            effective_blocks,
                            translated_texts,
                            target_language,
                            similarity_threshold=similarity_threshold,
                        )
                    yield f"event: complete\ndata: {json.dumps(result)}\n\n"
                    break
        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
