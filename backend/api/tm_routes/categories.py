from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.api.tm_routes.models import CategoryPayload
from backend.services.translation_memory_adapter import (
    create_tm_category,
    delete_tm_category,
    list_tm_categories,
    update_tm_category,
)

router = APIRouter()


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
