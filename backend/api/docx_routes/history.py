from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.api.pptx_history import delete_history_file, get_history_items

router = APIRouter()


@router.get("/history")
async def docx_history() -> dict:
    return {"items": get_history_items()}


@router.delete("/history/{filename:path}")
async def docx_delete_history(filename: str):
    import urllib.parse

    if "%" in filename:
        filename = urllib.parse.unquote(filename)
    if delete_history_file(filename):
        return {"status": "success", "message": "File deleted"}
    raise HTTPException(status_code=404, detail="File not found")
