"""
Export API endpoints for multi-format export functionality.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.services.export_formats import (
    export_to_docx,
    export_to_md,
    export_to_pdf,
    export_to_txt,
    export_to_xlsx,
    get_export_formats,
)
from backend.api.pptx_naming import generate_semantic_filename_with_ext
from backend.services.term_suggester import suggest_terms_for_blocks

router = APIRouter(prefix="/api")


class ExportRequest(BaseModel):
    blocks: list[dict[str, Any]]
    original_filename: str | None = "translation"
    mode: str = "translated"
    layout: str = "none"


class SuggestTermsRequest(BaseModel):
    blocks: list[dict[str, Any]]


@router.get("/export-formats")
async def list_export_formats():
    """Get list of available export formats."""
    return {"formats": get_export_formats()}


@router.post("/export/docx")
async def export_docx(request: ExportRequest):
    """Export translation blocks to Word document."""
    try:
        output = export_to_docx(request.blocks)
        fname = generate_semantic_filename_with_ext(
            request.original_filename, request.mode, request.layout, "docx"
        )
        safe_name = urllib.parse.quote(fname, safe="")
        return StreamingResponse(
            output,
            media_type=("application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{safe_name}",
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匯出失敗: {str(e)}") from e


@router.post("/export/xlsx")
async def export_xlsx(request: ExportRequest):
    """Export translation blocks to Excel spreadsheet."""
    try:
        output = export_to_xlsx(request.blocks)
        fname = generate_semantic_filename_with_ext(
            request.original_filename, request.mode, request.layout, "xlsx"
        )
        safe_name = urllib.parse.quote(fname, safe="")
        return StreamingResponse(
            output,
            media_type=("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{safe_name}",
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匯出失敗: {str(e)}") from e


@router.post("/export/txt")
async def export_txt(request: ExportRequest):
    """Export translation blocks to plain text file."""
    try:
        output = export_to_txt(request.blocks)
        fname = generate_semantic_filename_with_ext(
            request.original_filename, request.mode, request.layout, "txt"
        )
        safe_name = urllib.parse.quote(fname, safe="")
        return StreamingResponse(
            output,
            media_type="text/plain; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{safe_name}",
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匯出失敗: {str(e)}") from e


@router.post("/export/md")
async def export_md(request: ExportRequest):
    """Export translation blocks to Markdown file."""
    try:
        output = export_to_md(request.blocks)
        fname = generate_semantic_filename_with_ext(
            request.original_filename, request.mode, request.layout, "md"
        )
        safe_name = urllib.parse.quote(fname, safe="")
        return StreamingResponse(
            output,
            media_type="text/markdown; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{safe_name}",
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匯出失敗: {str(e)}") from e


@router.post("/export/pdf")
async def export_pdf(request: ExportRequest):
    """Export translation blocks to PDF document."""
    try:
        output = export_to_pdf(request.blocks)
        fname = generate_semantic_filename_with_ext(
            request.original_filename, request.mode, request.layout, "pdf"
        )
        safe_name = urllib.parse.quote(fname, safe="")
        return StreamingResponse(
            output,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{safe_name}",
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匯出失敗: {str(e)}") from e


@router.post("/suggest-terms")
async def suggest_terms(request: SuggestTermsRequest):
    """Analyze blocks and suggest terms for preservation or translation."""
    try:
        suggestions = suggest_terms_for_blocks(request.blocks)
        return {
            "suggestions": [
                {
                    "term": s.term,
                    "category": s.category,
                    "confidence": s.confidence,
                    "context": s.context,
                    "suggested_action": s.suggested_action,
                }
                for s in suggestions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失敗: {str(e)}") from e
