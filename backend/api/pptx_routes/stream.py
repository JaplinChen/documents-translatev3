from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.services.correction_mode import apply_correction_mode
from backend.services.translate_llm import (
    translate_blocks_async as translate_pptx_blocks_async,
)

from .models import TranslateRequest
from .utils import (
    _filter_effective_blocks,
    _parse_blocks,
    _prepare_blocks_for_correction,
    _resolve_completed_ids,
    _resolve_language,
    _resolve_param_overrides,
)

LOGGER = logging.getLogger(__name__)

router = APIRouter()


@router.post("/translate-stream")
async def pptx_translate_stream(  # noqa: C901
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
    scope_type = request.scope_type
    scope_id = request.scope_id
    domain = request.domain
    category = request.category

    completed_id_set = _resolve_completed_ids(completed_ids)

    LOGGER.debug(
        "[ENTRY_DEBUG] /translate-stream Blocks type: %s",
        type(blocks),
    )
    LOGGER.debug("[ENTRY_DEBUG] REFRESH: %s", refresh)

    blocks_data = _parse_blocks(blocks, "stream")

    if not target_language:
        raise HTTPException(status_code=400, detail="target_language 為必填")

    resolved_source_language = _resolve_language(
        blocks_data,
        source_language,
    )

    param_overrides = _resolve_param_overrides(provider, refresh, ollama_fast_mode)

    effective_blocks, skipped_count = _filter_effective_blocks(
        blocks_data, completed_id_set, refresh
    )

    if skipped_count > 0:
        LOGGER.info(
            "Resuming translation, skipping %s already completed blocks",
            skipped_count,
        )

    async def event_generator():
        queue = asyncio.Queue()

        async def progress_cb(progress_data):
            await queue.put({"event": "progress", "data": json.dumps(progress_data)})

        try:
            initial_data = json.dumps(
                {
                    "chunk_index": 0,
                    "completed_indices": [],
                    "chunk_size": 0,
                    "total_pending": len(blocks_data),
                    "timestamp": 0,
                }
            )
            yield f"event: progress\ndata: {initial_data}\n\n"

            task = asyncio.create_task(
                translate_pptx_blocks_async(
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
                    param_overrides={**param_overrides, "refresh": refresh},
                    on_progress=progress_cb,
                    mode=mode,
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

                    try:
                        export_dir = Path("data/exports")
                        export_dir.mkdir(parents=True, exist_ok=True)
                        ts = time.strftime("%Y%m%d-%H%M%S")
                        filename = f"autosave-{mode}-{ts}.json"
                        with open(
                            export_dir / filename,
                            "w",
                            encoding="utf-8",
                        ) as f:
                            json.dump(result, f, ensure_ascii=False, indent=2)
                        LOGGER.info("Auto-saved history to %s", filename)
                    except Exception as err:
                        LOGGER.error("Failed to auto-save history: %s", err)

                    break

        except Exception as exc:
            LOGGER.exception("Translation stream error")
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
