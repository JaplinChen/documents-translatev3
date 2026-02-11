from __future__ import annotations

from fastapi import APIRouter

from backend.api.download_utils import build_download_response

router = APIRouter()


@router.get("/download/{filename:path}")
async def docx_download(filename: str):
    return build_download_response(
        filename,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
