from __future__ import annotations

import asyncio
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.api.pptx_translate import TranslateRequest
from backend.contracts import coerce_blocks
from backend.services.correction_mode import apply_correction_mode, prepare_blocks_for_correction
from backend.services.language_detect import resolve_source_language
from backend.services.translate_llm import translate_blocks_async

router = APIRouter()


@router.post("/translate-stream")
async def docx_translate_stream(
    request: TranslateRequest,
) -> StreamingResponse:
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
    scope_type = request.scope_type
    scope_id = request.scope_id
    domain = request.domain
    category = request.category

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

    completed_id_set = set()
    if completed_ids:
        try:
            if isinstance(completed_ids, str):
                completed_id_set = set(json.loads(completed_ids))
            elif isinstance(completed_ids, list):
                completed_id_set = set(completed_ids)
        except (json.JSONDecodeError, TypeError):
            pass

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
            initial_payload = {
                "chunk_index": 0,
                "completed_indices": [],
                "chunk_size": 0,
                "total_pending": len(blocks_data),
                "timestamp": 0,
            }
            yield (
                f"event: progress\ndata: {json.dumps(initial_payload)}\n\n"
            )

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
                    scope_type=scope_type,
                    scope_id=scope_id,
                    domain=domain,
                    category=category,
                    param_overrides=param_overrides,
                    on_progress=progress_cb,
                )
            )

            while True:
                get_queue_task = asyncio.create_task(queue.get())
                done, _pending = await asyncio.wait(
                    [get_queue_task, task], return_when=asyncio.FIRST_COMPLETED
                )

                if get_queue_task in done:
                    event = get_queue_task.result()
                    yield (
                        f"event: {event['event']}\n"
                        f"data: {event['data']}\n\n"
                    )
                else:
                    get_queue_task.cancel()

                if task in done:
                    while not queue.empty():
                        event = queue.get_nowait()
                        yield (
                            f"event: {event['event']}\n"
                            f"data: {event['data']}\n\n"
                        )
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
                    yield (
                        f"event: complete\ndata: {json.dumps(result)}\n\n"
                    )
                    break
        except Exception as exc:
            yield (
                f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"
            )

    return StreamingResponse(event_generator(), media_type="text/event-stream")
