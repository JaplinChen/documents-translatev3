from __future__ import annotations

from fastapi import APIRouter, File, Response, UploadFile
from pydantic import BaseModel

from backend.services.translation_memory import (
    batch_delete_glossary,
    batch_delete_tm,
    clear_tm,
    delete_glossary,
    delete_tm,
    get_glossary,
    get_tm,
    seed_glossary,
    seed_tm,
    upsert_glossary,
    upsert_tm,
)

router = APIRouter(prefix="/api/tm")


class GlossaryEntry(BaseModel):
    """
    Glossary entry data structure for translation consistency.

    Attributes:
        source_lang: The source language code (e.g., 'vi').
        target_lang: The target language code (e.g., 'zh-TW').
        source_text: The term in the source language.
        target_text: The corresponding translation in the target language.
        priority: Relative priority for matching (default is 0).
    """
    model_config = {"extra": "ignore"}
    source_lang: str
    target_lang: str
    source_text: str
    target_text: str | None = ""
    priority: int | None = 0


class GlossaryDelete(BaseModel):
    id: int


class BatchDelete(BaseModel):
    ids: list[int]


class MemoryEntry(BaseModel):
    """
    Translation memory entry for reuse of previous translations.

    Attributes:
        source_lang: The source language code.
        target_lang: The target language code.
        source_text: Original source segment.
        target_text: Translated target segment.
    """
    model_config = {"extra": "ignore"}
    source_lang: str
    target_lang: str
    source_text: str
    target_text: str | None = ""


class MemoryDelete(BaseModel):
    id: int


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
    return {"items": get_glossary(limit=limit)}


@router.post("/glossary")
async def tm_glossary_upsert(entry: GlossaryEntry) -> dict:
    """
    Create or update a glossary entry.

    Args:
        entry: The glossary entry data.

    Returns:
        A dictionary with the operation status.
    """
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
    return {"items": get_tm(limit=limit)}


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
        priority = (
            int(parts[4])
            if len(parts) > 4 and parts[4].isdigit()
            else 0
        )
        entries.append(
            (source_lang, target_lang, source_text, target_text, priority)
        )
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
