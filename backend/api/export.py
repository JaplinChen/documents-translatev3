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
    export_to_pdf,
    export_to_txt,
    export_to_xlsx,
    get_export_formats,
)
from backend.services.term_suggester import suggest_terms_for_blocks

router = APIRouter(prefix="/api")


class ExportRequest(BaseModel):
    blocks: list[dict[str, Any]]


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
        return StreamingResponse(
            output,
            media_type=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            headers={
                "Content-Disposition": "attachment; filename=translation.docx"
            },
        )
    except ImportError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匯出失敗: {str(e)}") from e


@router.post("/export/xlsx")
async def export_xlsx(request: ExportRequest):
    """Export translation blocks to Excel spreadsheet."""
    try:
        output = export_to_xlsx(request.blocks)
        return StreamingResponse(
            output,
            media_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            headers={
                "Content-Disposition": "attachment; filename=translation.xlsx"
            },
        )
    except ImportError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匯出失敗: {str(e)}") from e


@router.post("/export/txt")
async def export_txt(request: ExportRequest):
    """Export translation blocks to plain text file."""
    try:
        output = export_to_txt(request.blocks)
        return StreamingResponse(
            output,
            media_type="text/plain; charset=utf-8",
            headers={
                "Content-Disposition": "attachment; filename=translation.txt"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匯出失敗: {str(e)}") from e


@router.post("/export/pdf")
async def export_pdf(request: ExportRequest):
    """Export translation blocks to PDF document."""
    try:
        output = export_to_pdf(request.blocks)
        return StreamingResponse(
            output,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=translation.pdf"
            },
        )
    except ImportError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
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
