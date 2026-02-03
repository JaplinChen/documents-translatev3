from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.api.terms_routes.models import CategoryPayload
from backend.services.term_repository import (
    create_category,
    delete_category,
    list_categories,
    update_category,
)

router = APIRouter()


@router.get("/categories")
async def category_list() -> dict:
    return {"items": list_categories()}


@router.post("/categories")
async def category_create(payload: CategoryPayload) -> dict:
    try:
        item = create_category(payload.name, payload.sort_order)
        return {"item": item}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/categories/{category_id}")
async def category_update(category_id: int, payload: CategoryPayload) -> dict:
    try:
        item = update_category(category_id, payload.name, payload.sort_order)
        return {"item": item}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/categories/{category_id}")
async def category_delete(category_id: int) -> dict:
    try:
        delete_category(category_id)
        return {"status": "ok"}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
