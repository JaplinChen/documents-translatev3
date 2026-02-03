from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.api.terms_routes.models import BatchPayload
from backend.services.term_repository import batch_delete_terms, batch_update_terms

router = APIRouter()


@router.post("/batch")
async def term_batch_update(payload: BatchPayload) -> dict:
    try:
        updated = batch_update_terms(
            payload.ids,
            category_id=payload.category_id,
            status=payload.status,
            case_rule=payload.case_rule,
            source=payload.source,
            priority=payload.priority,
        )
        return {"updated": updated}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/batch")
async def term_batch_delete(payload: BatchPayload) -> dict:
    deleted = batch_delete_terms(payload.ids)
    return {"deleted": deleted}
