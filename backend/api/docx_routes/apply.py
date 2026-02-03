from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.api.error_handler import api_error_handler, validate_json_blocks
from backend.api.pptx_naming import generate_semantic_filename
from backend.services.docx.apply import (
    apply_bilingual,
    apply_chinese_corrections,
    apply_translations,
)

router = APIRouter()


@router.post("/apply")
@api_error_handler(validate_file=False)
async def docx_apply(
    file: UploadFile = File(...),
    blocks: str = Form(...),
    mode: str = Form("bilingual"),
    target_language: str | None = Form(None),
) -> dict:
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="只支援 .docx 檔案")

    docx_bytes = await file.read()
    blocks_data = validate_json_blocks(blocks)

    if mode not in {"bilingual", "correction", "translated"}:
        raise HTTPException(status_code=400, detail="不支援的 mode")

    with tempfile.TemporaryDirectory() as temp_dir:
        out_p = os.path.join(temp_dir, "out.docx")

        if mode == "bilingual":
            apply_bilingual(
                docx_bytes,
                out_p,
                blocks_data,
                target_language=target_language,
            )
        elif mode == "translated":
            apply_translations(
                docx_bytes,
                out_p,
                blocks_data,
                mode="direct",
                target_language=target_language,
            )
        else:
            apply_chinese_corrections(docx_bytes, out_p, blocks_data)

        with open(out_p, "rb") as h:
            output_bytes = h.read()

    final_filename = generate_semantic_filename(file.filename, mode, "inline")
    if not final_filename.endswith(".docx"):
        final_filename = final_filename.rsplit(".", 1)[0] + ".docx"

    save_path = Path("data/exports") / final_filename
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(output_bytes)

    import urllib.parse

    safe_uri = urllib.parse.quote(final_filename, safe="")
    return {
        "status": "success",
        "filename": final_filename,
        "download_url": f"/api/docx/download/{safe_uri}",
    }
