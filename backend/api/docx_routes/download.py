from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/download/{filename:path}")
async def docx_download(filename: str):
    import urllib.parse

    file_path = Path("data/exports") / filename
    if not file_path.exists():
        alt_path = Path("data/exports") / urllib.parse.unquote(filename)
        if alt_path.exists():
            file_path = alt_path
        else:
            raise HTTPException(status_code=404, detail="檔案不存在")

    actual_filename = file_path.name
    ascii_name = "".join(c if ord(c) < 128 else "_" for c in actual_filename)
    safe_name = urllib.parse.quote(actual_filename, safe="")
    content_disposition = (
        f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{safe_name}'
    )

    return FileResponse(
        path=file_path,
        media_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        headers={
            "Content-Disposition": content_disposition,
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Cache-Control": "no-cache",
        },
    )
