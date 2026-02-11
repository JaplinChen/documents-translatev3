from __future__ import annotations

import urllib.parse
from pathlib import Path
from typing import Callable

from fastapi import HTTPException
from fastapi.responses import FileResponse

MediaTypeResolver = Callable[[Path], str]


def _resolve_export_path(filename: str) -> Path:
    file_path = Path("data/exports") / filename
    if file_path.exists():
        return file_path

    alt_path = Path("data/exports") / urllib.parse.unquote(filename)
    if alt_path.exists():
        return alt_path

    raise HTTPException(status_code=404, detail="檔案不存在")


def build_download_response(
    filename: str,
    media_type: str | MediaTypeResolver,
) -> FileResponse:
    file_path = _resolve_export_path(filename)
    actual_filename = file_path.name

    ascii_name = "".join(c if ord(c) < 128 else "_" for c in actual_filename)
    safe_name = urllib.parse.quote(actual_filename, safe="")
    content_disposition = (
        f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{safe_name}'
    )

    resolved_media_type = media_type(file_path) if callable(media_type) else media_type

    return FileResponse(
        path=file_path,
        media_type=resolved_media_type,
        headers={
            "Content-Disposition": content_disposition,
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Cache-Control": "no-cache",
        },
    )
