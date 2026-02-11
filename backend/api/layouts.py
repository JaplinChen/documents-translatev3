from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.layout_registry import (
    delete_custom_layout,
    get_custom_layout,
    import_custom_layouts,
    list_custom_layouts,
    list_layouts,
    preview_import_custom_layouts,
    upsert_custom_layout,
)

router = APIRouter(prefix="/api/layouts")


class LayoutUpsertRequest(BaseModel):
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    file_type: str = Field(..., pattern="^(pptx|xlsx|docx|pdf)$")
    modes: list[str] = Field(default_factory=lambda: ["bilingual"])
    apply_value: str = Field(..., min_length=1)
    enabled: bool = True
    params_schema: dict[str, Any] = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
        }
    )


class LayoutPatchRequest(BaseModel):
    name: str | None = None
    enabled: bool | None = None
    apply_value: str | None = None
    modes: list[str] | None = None
    params_schema: dict[str, Any] | None = None


class LayoutImportRequest(BaseModel):
    layouts: list[dict[str, Any]] = Field(default_factory=list)
    mode: str = Field(default="merge", pattern="^(merge|replace)$")
    file_type: str | None = Field(default=None, pattern="^(pptx|xlsx|docx|pdf)$")
    decisions: dict[str, str] = Field(default_factory=dict)


@router.get("")
async def get_layouts(
    file_type: str | None = None,
    mode: str | None = None,
    include_disabled: bool = False,
) -> dict[str, Any]:
    return {
        "layouts": list_layouts(
            file_type=file_type,
            mode=mode,
            include_disabled=include_disabled,
        ),
    }


@router.post("/custom")
async def upsert_layout(payload: LayoutUpsertRequest) -> dict[str, Any]:
    payload_data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    try:
        data = upsert_custom_layout(payload_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "success", "layout": data}


@router.get("/custom/export")
async def export_custom_layouts(file_type: str | None = None) -> dict[str, Any]:
    return {
        "layouts": list_custom_layouts(file_type=file_type),
    }


@router.post("/custom/import")
async def import_layouts(payload: LayoutImportRequest) -> dict[str, Any]:
    payload_data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    try:
        result = import_custom_layouts(
            layouts=payload_data.get("layouts", []),
            mode=payload_data.get("mode", "merge"),
            file_type=payload_data.get("file_type"),
            decisions=payload_data.get("decisions") or {},
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "success", **result}


@router.post("/custom/import-preview")
async def import_layouts_preview(payload: LayoutImportRequest) -> dict[str, Any]:
    payload_data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    try:
        result = preview_import_custom_layouts(
            layouts=payload_data.get("layouts", []),
            mode=payload_data.get("mode", "merge"),
            file_type=payload_data.get("file_type"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "success", **result}


@router.patch("/custom/{file_type}/{layout_id}")
async def patch_layout(
    file_type: str,
    layout_id: str,
    payload: LayoutPatchRequest,
) -> dict[str, Any]:
    current = get_custom_layout(file_type=file_type, layout_id=layout_id)
    if not current:
        raise HTTPException(status_code=404, detail="找不到自訂版面")

    patch_data = payload.model_dump(exclude_none=True) if hasattr(payload, "model_dump") else payload.dict(exclude_none=True)
    merged = dict(current)
    merged.update(patch_data)
    try:
        updated = upsert_custom_layout(merged)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "success", "layout": updated}


@router.delete("/custom/{file_type}/{layout_id}")
async def remove_layout(file_type: str, layout_id: str) -> dict[str, Any]:
    ok = delete_custom_layout(file_type=file_type, layout_id=layout_id)
    if not ok:
        raise HTTPException(status_code=404, detail="找不到自訂版面")
    return {"status": "success"}
