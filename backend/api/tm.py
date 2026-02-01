from __future__ import annotations

from fastapi import APIRouter, File, Response, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
import json
import asyncio
from pydantic import BaseModel

from backend.services.translation_memory import (
    batch_delete_glossary,
    batch_delete_tm,
    clear_tm,
    delete_glossary,
    delete_tm,
    get_glossary,
    get_glossary_count,
    get_tm,
    get_tm_count,
    seed_glossary,
    seed_tm,
    upsert_glossary,
    upsert_tm,
    list_tm_categories,
    create_tm_category,
    update_tm_category,
    delete_tm_category,
)

from backend.services.learning_service import record_term_feedback

router = APIRouter(prefix="/api/tm")


class GlossaryEntry(BaseModel):
    """
    Glossary entry data structure for translation consistency.
    """

    model_config = {"extra": "ignore"}
    id: int | None = None
    source_lang: str
    target_lang: str
    source_text: str
    target_text: str | None = ""
    priority: int | None = 0
    category_id: int | None = None


class GlossaryDelete(BaseModel):
    id: int


class BatchDelete(BaseModel):
    ids: list[int]


class MemoryEntry(BaseModel):
    """
    Translation memory entry for reuse of previous translations.
    """

    model_config = {"extra": "ignore"}
    id: int | None = None
    source_lang: str
    target_lang: str
    source_text: str
    target_text: str | None = ""
    category_id: int | None = None


class MemoryDelete(BaseModel):
    id: int


class CategoryPayload(BaseModel):
    name: str
    sort_order: int | None = 0


@router.post("/seed")
async def tm_seed() -> dict:
    seed_glossary(
        [
            ("vi", "zh-TW", "báo cáo", "報告", 10),
            ("vi", "zh-TW", "đề xuất", "提案", 9),
            ("vi", "zh-TW", "cải thiện", "改善", 8),
        ]
    )
    seed_tm(
        [
            ("vi", "zh-TW", "lợi ích", "利益"),
            ("vi", "zh-TW", "chi phí", "成本"),
            ("vi", "zh-TW", "đề xuất cải thiện", "改善建議"),
        ]
    )
    return {"status": "seeded"}


@router.get("/glossary")
async def tm_glossary(limit: int = 200) -> dict:
    return {
        "items": get_glossary(limit=limit),
        "total": get_glossary_count(),
        "limit": limit,
    }


@router.post("/glossary")
async def tm_glossary_upsert(entry: GlossaryEntry) -> dict:
    upsert_glossary(entry.model_dump())
    return {"status": "ok"}


@router.post("/glossary/batch")
async def tm_glossary_batch(entries: list[GlossaryEntry]) -> dict:
    from backend.services.translation_memory import batch_upsert_glossary

    batch_upsert_glossary([e.model_dump() for e in entries])
    return {"status": "ok", "count": len(entries)}


@router.delete("/glossary/clear")
async def tm_glossary_clear() -> dict:
    from backend.services.translation_memory import clear_glossary

    deleted = clear_glossary()
    return {"deleted": deleted}


@router.delete("/glossary")
async def tm_glossary_delete(entry: GlossaryDelete) -> dict:
    deleted = delete_glossary(entry.id)
    return {"deleted": deleted}


@router.delete("/glossary/batch")
async def tm_glossary_batch_delete(payload: BatchDelete) -> dict:
    deleted = batch_delete_glossary(payload.ids)
    return {"deleted": deleted}


@router.get("/memory")
async def tm_memory(limit: int = 200) -> dict:
    return {
        "items": get_tm(limit=limit),
        "total": get_tm_count(),
        "limit": limit,
    }


@router.post("/memory")
async def tm_memory_upsert(entry: MemoryEntry) -> dict:
    upsert_tm(entry.model_dump())
    return {"status": "ok"}


@router.delete("/memory")
async def tm_memory_delete(entry: MemoryDelete) -> dict:
    deleted = delete_tm(entry.id)
    return {"deleted": deleted}


@router.delete("/memory/batch")
async def tm_memory_batch_delete(payload: BatchDelete) -> dict:
    deleted = batch_delete_tm(payload.ids)
    return {"deleted": deleted}


@router.delete("/memory/clear")
async def tm_memory_clear() -> dict:
    deleted = clear_tm()
    return {"deleted": deleted}


@router.post("/glossary/import")
async def tm_glossary_import(file: UploadFile = File(...)) -> dict:
    content = (await file.read()).decode("utf-8")
    entries = []
    for line in content.splitlines():
        if not line.strip():
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 4:
            continue
        source_lang, target_lang, source_text, target_text = parts[:4]
        priority = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0
        entries.append((source_lang, target_lang, source_text, target_text, priority))
    seed_glossary(entries)
    return {"status": "ok", "count": len(entries)}


@router.post("/memory/import")
async def tm_memory_import(file: UploadFile = File(...)) -> dict:
    content = (await file.read()).decode("utf-8")
    entries = []
    for line in content.splitlines():
        if not line.strip():
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 4:
            continue
        source_lang, target_lang, source_text, target_text = parts[:4]
        entries.append((source_lang, target_lang, source_text, target_text))
    seed_tm(entries)
    return {"status": "ok", "count": len(entries)}


@router.get("/glossary/export")
async def tm_glossary_export() -> Response:
    items = get_glossary(limit=1000)
    lines = ["source_lang,target_lang,source_text,target_text,priority"]
    for item in items:
        lines.append(
            f"{item['source_lang']},{item['target_lang']},"
            f"{item['source_text']},{item['target_text']},{item['priority']}"
        )
    return Response(content="\n".join(lines), media_type="text/csv")


@router.get("/memory/export")
async def tm_memory_export() -> Response:
    items = get_tm(limit=1000)
    lines = ["source_lang,target_lang,source_text,target_text"]
    for item in items:
        lines.append(
            f"{item['source_lang']},{item['target_lang']},"
            f"{item['source_text']},{item['target_text']}"
        )
    return Response(content="\n".join(lines), media_type="text/csv")


# Category endpoints


@router.get("/categories")
async def tm_category_list() -> dict:
    return {"items": list_tm_categories()}


@router.post("/categories")
async def tm_category_create(payload: CategoryPayload) -> dict:
    try:
        item = create_tm_category(payload.name, payload.sort_order)
        return {"item": item}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/categories/{category_id}")
async def tm_category_update(category_id: int, payload: CategoryPayload) -> dict:
    try:
        item = update_tm_category(category_id, payload.name, payload.sort_order)
        return {"item": item}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/categories/{category_id}")
async def tm_category_delete(category_id: int) -> dict:
    delete_tm_category(category_id)
    return {"status": "ok"}


# Unified Glossary Extraction


class GlossaryExtractPayload(BaseModel):
    blocks: list[dict]
    target_language: str = "zh-TW"
    provider: str | None = None
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None


@router.post("/extract-glossary")
async def tm_extract_glossary(payload: GlossaryExtractPayload) -> dict:
    """
    Unified terminology extraction for all file types (PPTX, DOCX, XLSX).
    Uses JSON instead of Form for stability with large block lists.
    """
    from backend.services.glossary_extraction import extract_glossary_terms

    try:
        result = extract_glossary_terms(
            payload.blocks,
            payload.target_language,
            provider=payload.provider,
            model=payload.model,
            api_key=payload.api_key,
            base_url=payload.base_url,
        )
        return result
    except Exception as exc:
        # Log and return error details so frontend can surface it
        import traceback

        traceback.print_exc()
        return {"terms": [], "error": str(exc)}


@router.post("/extract-glossary-stream")
async def tm_extract_glossary_stream(payload: GlossaryExtractPayload) -> StreamingResponse:
    """
    Streaming version of terminology extraction.
    Reports progress via SSE while analyzing document segments.
    """
    from backend.services.glossary_extraction import extract_glossary_terms
    from fastapi.responses import StreamingResponse
    import asyncio
    import json

    async def event_generator():
        try:
            blocks = payload.blocks
            total_blocks = len(blocks)

            # Divide blocks into 3 representative segments (start, middle, end)
            # to get a good spread of terminology with minimal LLM calls.
            segments = []
            if total_blocks <= 20:
                segments = [blocks]
            else:
                chunk_size = min(20, total_blocks // 3) if total_blocks > 0 else 0
                if chunk_size > 0:
                    segments.append(blocks[:chunk_size])
                    mid = total_blocks // 2
                    segments.append(blocks[mid : mid + chunk_size])
                    segments.append(blocks[-chunk_size:])
                else:
                    segments = [blocks]

            all_terms = []
            num_segments = len(segments)

            yield f"event: progress\ndata: {json.dumps({'message': '正在準備分析文本...', 'percent': 10})}\n\n"
            await asyncio.sleep(0.1)

            for i, segment in enumerate(segments):
                stage_name = f"正在分析第 {i + 1}/{num_segments} 段文本..."
                percent = int(10 + (i / num_segments) * 80)
                yield f"event: progress\ndata: {json.dumps({'message': stage_name, 'percent': percent})}\n\n"

                # Run extraction for this segment in a thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    extract_glossary_terms,
                    segment,
                    payload.target_language,
                    payload.provider,
                    payload.model,
                    payload.api_key,
                    payload.base_url,
                )

                terms = result.get("terms", [])
                domain = result.get("domain", "general")

                if terms and isinstance(terms, list):
                    all_terms.extend(terms)

            # De-duplicate terms by source text (case-insensitive)
            unique_terms_map = {}
            for t in all_terms:
                if not isinstance(t, dict) or "source" not in t:
                    continue
                key = t["source"].strip().lower()
                if key not in unique_terms_map:
                    unique_terms_map[key] = t

            final_terms = list(unique_terms_map.values())

            yield f"event: progress\ndata: {json.dumps({'message': '完成分析，正在彙整術語...', 'percent': 95})}\n\n"
            await asyncio.sleep(0.5)

            payload_data = {"terms": final_terms, "domain": domain}
            yield f"event: complete\ndata: {json.dumps(payload_data)}\n\n"

        except Exception as exc:
            import traceback

            traceback.print_exc()
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


class TermFeedbackPayload(BaseModel):
    source: str
    target: str
    source_lang: str | None = None
    target_lang: str | None = "zh-TW"


@router.post("/feedback")
async def tm_record_feedback(payload: TermFeedbackPayload) -> dict:
    """
    Record user feedback for terminology learning.
    """
    try:
        record_term_feedback(
            payload.source, payload.target, payload.source_lang, payload.target_lang
        )
        return {"status": "recorded"}
    except Exception as e:
        import logging

        logging.getLogger(__name__).error(f"Feedback recording failed: {e}")
        return {"status": "error", "message": str(e)}
