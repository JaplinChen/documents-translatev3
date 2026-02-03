from __future__ import annotations

from fastapi import APIRouter, File, Response, UploadFile

from backend.api.tm_routes.models import BatchDelete, GlossaryDelete, GlossaryEntry
from backend.services.translation_memory_adapter import (
    batch_delete_glossary,
    delete_glossary,
    get_glossary,
    get_glossary_count,
    seed_glossary,
    upsert_glossary,
)

router = APIRouter()


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
    from backend.services.translation_memory_adapter import batch_upsert_glossary

    batch_upsert_glossary([e.model_dump() for e in entries])
    return {"status": "ok", "count": len(entries)}


@router.delete("/glossary/clear")
async def tm_glossary_clear() -> dict:
    from backend.services.translation_memory_adapter import clear_glossary

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
