from __future__ import annotations

from fastapi import APIRouter, File, Response, UploadFile

from backend.api.tm_routes.models import BatchDelete, MemoryDelete, MemoryEntry
from backend.services.translation_memory_adapter import (
    batch_delete_tm,
    clear_tm,
    delete_tm,
    get_tm,
    get_tm_count,
    seed_tm,
    upsert_tm,
)

router = APIRouter()


@router.get("/memory")
async def tm_memory(limit: int = 200, offset: int = 0) -> dict:
    return {
        "items": get_tm(limit=limit, offset=offset),
        "total": get_tm_count(),
        "limit": limit,
        "offset": offset,
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
