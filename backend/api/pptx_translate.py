"""PPTX translation API endpoints.

This module provides REST API endpoints for translating PPTX content.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.config import settings
from backend.contracts import coerce_blocks
from backend.services.correction_mode import (
    apply_correction_mode,
    prepare_blocks_for_correction,
)
from backend.services.language_detect import resolve_source_language
from backend.services.llm_errors import (
    build_connection_refused_message,
    is_connection_refused,
)
from backend.services.translate_llm import (
    translate_blocks_async as translate_pptx_blocks_async,
)

LOGGER = logging.getLogger(__name__)
VI_REGEX = re.compile(
    r"[đĐàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ]",
    re.I,
)

router = APIRouter(prefix="/api/pptx")


class TranslateRequest(BaseModel):
    blocks: str | list[dict]
    source_language: str | None = None
    target_language: str
    secondary_language: str | None = None
    mode: str = "bilingual"
    use_tm: bool = False
    provider: str | None = None
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    ollama_fast_mode: bool = False
    tone: str | None = None
    vision_context: bool = True
    smart_layout: bool = True
    refresh: bool = False
    completed_ids: str | list[str] | list[int] | None = None
    similarity_threshold: float = 0.75


def _prepare_blocks_for_correction(
    items: list[dict],
    target_language: str | None,
) -> list[dict]:
    """Prepare blocks for correction mode.

    Skip blocks that match the target language.
    """
    return prepare_blocks_for_correction(items, target_language)


@router.post("/translate")
async def pptx_translate(
    request: TranslateRequest,
) -> dict:
    """Translate text blocks using LLM."""
    llm_mode = settings.translate_llm_mode
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
    similarity_threshold = request.similarity_threshold

    try:
        if isinstance(blocks, str):
            blocks_data = coerce_blocks(json.loads(blocks))
        else:
            blocks_data = coerce_blocks(blocks)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="blocks JSON 無效") from exc
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="blocks 資料無效 (translate)",
        ) from exc

    if not target_language:
        raise HTTPException(status_code=400, detail="target_language 為必填")

    resolved_source_language = resolve_source_language(
        blocks_data,
        source_language,
    )

    param_overrides = {"refresh": refresh}
    if (provider or "").lower() == "ollama" and ollama_fast_mode:
        param_overrides.update(
            {
                "single_request": False,
                "chunk_size": 1,
                "chunk_delay": 0.0,
            }
        )

    try:
        translated = await translate_pptx_blocks_async(
            _prepare_blocks_for_correction(blocks_data, target_language)
            if mode == "correction"
            else blocks_data,
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
            param_overrides={**param_overrides, "refresh": refresh},
        )
    except Exception as exc:
        if provider == "ollama" and is_connection_refused(exc):
            raise HTTPException(
                status_code=400,
                detail=build_connection_refused_message(
                    "Ollama",
                    base_url or "http://localhost:11434",
                ),
            ) from exc
        error_msg = str(exc)
        if "image" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail=(
                    "翻譯失敗：偵測到圖片相關錯誤。您的 PPTX 可能包含圖片，"
                    "目前所選模型不支援圖片輸入。請在 LLM 設定中改用支援視覺模型"
                    "（例如 GPT-4o）。"
                ),
            ) from exc
        raise HTTPException(status_code=400, detail=error_msg) from exc

    result_blocks = translated.get("blocks", [])
    if mode == "correction":
        translated_texts = [b.get("translated_text", "") for b in result_blocks]
        result_blocks = apply_correction_mode(
            blocks_data,
            translated_texts,
            target_language,
            similarity_threshold=similarity_threshold,
        )

    return {
        "mode": mode,
        "source_language": resolved_source_language or source_language,
        "target_language": target_language,
        "blocks": result_blocks,
        "llm_mode": llm_mode,
        "warning": "目前為 mock 模式，翻譯結果會回填原文。" if llm_mode == "mock" else None,
    }


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

    LOGGER.debug(
        "[ENTRY_DEBUG] /translate-stream Blocks type: %s",
        type(blocks),
    )
    LOGGER.debug("[ENTRY_DEBUG] REFRESH: %s", refresh)

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
    if (provider or "").lower() == "ollama" and ollama_fast_mode:
        param_overrides.update(
            {
                "single_request": False,
                "chunk_size": 1,
                "chunk_delay": 0.0,
            }
        )

    # 執行過濾：跳過已翻譯且不在 refresh 模式下的區塊
    effective_blocks = []
    skipped_count = 0
    for b in blocks_data:
        text = b.get("source_text", "")
        has_vi = bool(VI_REGEX.search(text))

        # 核心修正：如果是混排區塊且處於 refresh 模式，
        # 強制進入處理隊列，確保 LLM 執行雙語保留指令
        if refresh and has_vi:
            effective_blocks.append(b)
            continue

        # 如果 block 有 client_id 且在已完成名單中，且不是強制重新整理，則跳過
        if not refresh and b.get("client_id") in completed_id_set:
            skipped_count += 1
            continue
        effective_blocks.append(b)

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
            # yield initial progress event immediately to switch UI status
            # This ensures headers are sent before any potential blocking
            # initialization.
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
                    # Flush any remaining items in queue regardless of
                    # task status.
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

                    # Auto-save to history (JSON only) for immediate visibility
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
