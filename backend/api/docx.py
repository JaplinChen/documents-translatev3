"""DOCX API endpoints.

This module provides REST API endpoints for DOCX file extraction and
application.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Body
from fastapi.responses import FileResponse, StreamingResponse

from backend.api.error_handler import api_error_handler, validate_json_blocks
from backend.api.pptx_history import delete_history_file, get_history_items
from backend.api.pptx_naming import generate_semantic_filename_with_ext
from backend.api.pptx_translate import TranslateRequest
from backend.api.pptx_utils import validate_file_type
from backend.contracts import coerce_blocks
from backend.services.correction_mode import (
    apply_correction_mode,
    prepare_blocks_for_correction,
)
from backend.services.docx.apply import (
    apply_bilingual,
    apply_chinese_corrections,
    apply_translations,
)
from backend.services.docx.extract import extract_blocks as extract_docx_blocks
from backend.services.document_cache import doc_cache
from backend.services.language_detect import (
    detect_document_languages,
    resolve_source_language,
)
from backend.services.translate_llm import translate_blocks_async

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/api/docx")


@router.post("/extract")
@api_error_handler(validate_file=False, read_error_msg="DOCX 檔案無效")
async def docx_extract(
    file: UploadFile = File(...),
    refresh: bool = False,
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

    data = extract_docx_blocks(docx_bytes)
    blocks = data["blocks"]
    sw = data["slide_width"]
    sh = data["slide_height"]

    # 更新快取
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
            apply_bilingual(
                docx_bytes,
                out_p,
                blocks_data,
                target_language=target_language,
            )
        elif mode == "translated":
            apply_translations(
                docx_bytes,
                out_p,
                blocks_data,
                mode="direct",
                target_language=target_language,
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
    content_disposition = f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{safe_name}"

    return FileResponse(
        path=file_path,
        media_type=("application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        headers={
            "Content-Disposition": content_disposition,
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Cache-Control": "no-cache",
        },
    )


@router.get("/history")
async def docx_history() -> dict:
    return {"items": get_history_items()}


@router.delete("/history/{filename:path}")
async def docx_delete_history(filename: str):
    import urllib.parse

    if "%" in filename:
        filename = urllib.parse.unquote(filename)
    if delete_history_file(filename):
        return {"status": "success", "message": "File deleted"}
    raise HTTPException(status_code=404, detail="File not found")


@router.post("/translate-stream")
async def docx_translate_stream(  # noqa: C901
    request: TranslateRequest,
) -> StreamingResponse:
    """Translate text blocks and stream progress via SSE."""
    blocks = request.blocks
    source_language = request.source_language
    target_language = request.target_language
    mode = request.mode
    use_tm = request.use_tm
    provider = request.provider
    model = request.model
    api_key = request.api_key
    base_url = request.base_url
    ollama_fast_mode = request.ollama_fast_mode
    tone = request.tone
    vision_context = request.vision_context
    smart_layout = request.smart_layout
    refresh = request.refresh
    completed_ids = request.completed_ids
    similarity_threshold = request.similarity_threshold

    try:
        if isinstance(blocks, str):
            blocks_data = coerce_blocks(json.loads(blocks))
        else:
            blocks_data = coerce_blocks(blocks)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="blocks 資料無效") from exc

    if not target_language:
        raise HTTPException(status_code=400, detail="target_language 為必填")

    resolved_source_language = resolve_source_language(
        blocks_data,
        source_language,
    )
    param_overrides = {"refresh": refresh}

    # 解析已完成的 ID 列表
    completed_id_set = set()
    if completed_ids:
        try:
            if isinstance(completed_ids, str):
                completed_id_set = set(json.loads(completed_ids))
            elif isinstance(completed_ids, list):
                completed_id_set = set(completed_ids)
        except (json.JSONDecodeError, TypeError):
            pass

    # 執行過濾
    effective_blocks = []
    for b in blocks_data:
        if not refresh and b.get("client_id") in completed_id_set:
            continue
        effective_blocks.append(b)

    def _prepare_blocks_for_correction(
        items: list[dict],
        target_lang: str | None,
    ) -> list[dict]:
        return prepare_blocks_for_correction(items, target_lang)

    async def event_generator():
        queue = asyncio.Queue()

        async def progress_cb(progress_data):
            await queue.put({"event": "progress", "data": json.dumps(progress_data)})

        try:
            # yield initial progress
            initial_payload = {
                "chunk_index": 0,
                "completed_indices": [],
                "chunk_size": 0,
                "total_pending": len(blocks_data),
                "timestamp": 0,
            }
            yield (f"event: progress\ndata: {json.dumps(initial_payload)}\n\n")

            task = asyncio.create_task(
                translate_blocks_async(
                    _prepare_blocks_for_correction(
                        effective_blocks,
                        target_language,
                    )
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
                    yield (f"event: {event['event']}\ndata: {event['data']}\n\n")
                else:
                    get_queue_task.cancel()

                if task in done:
                    while not queue.empty():
                        event = queue.get_nowait()
                        yield (f"event: {event['event']}\ndata: {event['data']}\n\n")
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
