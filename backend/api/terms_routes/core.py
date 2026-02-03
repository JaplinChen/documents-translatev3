from __future__ import annotations

import socket

from fastapi import APIRouter, HTTPException, Request

from backend.api.terms_routes.models import TermPayload
from backend.services.term_repository import (
    create_term,
    delete_term,
    list_terms,
    list_versions,
    update_term,
    upsert_term_by_norm,
)

router = APIRouter()


@router.get("/")
async def term_list(
    q: str | None = None,
    category_id: int | None = None,
    status: str | None = None,
    missing_lang: str | None = None,
    has_alias: bool | None = None,
    created_by: str | None = None,
    filename: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    items = list_terms(
        {
            "q": q,
            "category_id": category_id,
            "status": status,
            "missing_lang": missing_lang,
            "has_alias": has_alias,
            "created_by": created_by,
            "filename": filename,
            "date_from": date_from,
            "date_to": date_to,
        }
    )
    return {"items": items}


def _ensure_created_by(payload: TermPayload, request: Request) -> None:
    if payload.created_by:
        return
    client_host = request.client.host
    try:
        hostname, _, _ = socket.gethostbyaddr(client_host)
        payload.created_by = hostname
    except Exception:
        payload.created_by = client_host


@router.post("/")
async def term_create(payload: TermPayload, request: Request) -> dict:
    try:
        _ensure_created_by(payload, request)
        item = create_term(payload.model_dump())
        return {"item": item}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/upsert")
async def term_upsert(payload: TermPayload, request: Request) -> dict:
    try:
        _ensure_created_by(payload, request)
        item = upsert_term_by_norm(payload.model_dump())
        return {"item": item}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/{term_id}")
async def term_update(term_id: int, payload: TermPayload) -> dict:
    try:
        item = update_term(term_id, payload.model_dump())
        return {"item": item}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{term_id}")
async def term_delete(term_id: int) -> dict:
    try:
        delete_term(term_id)
        return {"status": "ok"}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{term_id}/versions")
async def term_versions(term_id: int) -> dict:
    items = list_versions(term_id)
    return {"items": items}
