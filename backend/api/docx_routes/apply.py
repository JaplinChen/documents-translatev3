from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.api.error_handler import api_error_handler, validate_json_blocks
from backend.api.pptx_naming import generate_semantic_filename
from backend.services.layout_registry import resolve_layout_apply_value
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
    bilingual_layout: str = Form("inline"),
    layout_id: str | None = Form(None),
    layout_params: str | None = Form(None),
    target_language: str | None = Form(None),
) -> dict:
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="只支援 .docx 檔案")

    docx_bytes = await file.read()
    blocks_data = validate_json_blocks(blocks)
    parsed_layout_params: dict = {}
    if layout_params:
        try:
            maybe_obj = json.loads(layout_params)
            if isinstance(maybe_obj, dict):
                parsed_layout_params = maybe_obj
        except Exception:
            parsed_layout_params = {}

    if mode not in {"bilingual", "correction", "translated"}:
        raise HTTPException(status_code=400, detail="不支援的 mode")
    apply_layout = resolve_layout_apply_value(
        layout_id=layout_id,
        file_type="docx",
        mode=mode,
        fallback_value=bilingual_layout,
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        out_p = os.path.join(temp_dir, "out.docx")

        if mode == "bilingual":
            apply_bilingual(
                docx_bytes,
                out_p,
                blocks_data,
                layout=apply_layout,
                target_language=target_language,
                layout_params=parsed_layout_params,
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

    final_filename = generate_semantic_filename(file.filename, mode, apply_layout)
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
