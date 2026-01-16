from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Response

from backend.contracts import coerce_blocks
from backend.services.language_detect import (
    detect_document_languages,
    detect_language,
    resolve_source_language,
)
from backend.services.pptx_apply import (
    apply_bilingual,
    apply_chinese_corrections,
    apply_translations,
)
from backend.services.pptx_extract import extract_blocks as extract_pptx_blocks
from backend.services.translate_llm import translate_blocks as translate_pptx_blocks
from backend.services.llm_errors import (
    build_connection_refused_message,
    is_connection_refused,
)

router = APIRouter(prefix="/api/pptx")

SUPPORTED_EXTENSIONS = {".pptx", ".docx"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}


def _get_file_extension(filename: str | None) -> str:
    if not filename or "." not in filename:
        return ""
    return "." + filename.lower().split(".")[-1]


def _validate_file_type(filename: str | None) -> tuple[bool, str]:
    if not filename:
        return False, "請選擇檔案"

    ext = _get_file_extension(filename)

    if ext in IMAGE_EXTENSIONS:
        return (
            False,
            (
                f"不支援圖片檔案 ({filename})。此工具只支援翻譯 PPTX 或 DOCX "
                "檔案中的文字內容。若需翻譯圖片文字，請改用支援視覺模型的 LLM API "
                "(例如 GPT-4o)。"
            ),
        )

    if ext not in SUPPORTED_EXTENSIONS:
        return False, f"不支援的檔案格式 ({ext})，僅支援 .pptx 或 .docx"

    return True, ""


@router.post("/extract")
async def pptx_extract(file: UploadFile = File(...)) -> dict:
    valid, error_msg = _validate_file_type(file.filename)
    if not valid:
        raise HTTPException(status_code=400, detail=error_msg)

    try:
        pptx_bytes = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="PPTX 檔案無效") from exc

    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, "input.pptx")
        with open(input_path, "wb") as handle:
            handle.write(pptx_bytes)
        blocks = extract_pptx_blocks(input_path)

    language_summary = detect_document_languages(blocks)
    return {"blocks": blocks, "language_summary": language_summary}


@router.post("/languages")
async def pptx_languages(file: UploadFile = File(...)) -> dict:
    valid, error_msg = _validate_file_type(file.filename)
    if not valid:
        raise HTTPException(status_code=400, detail=error_msg)
    try:
        pptx_bytes = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="PPTX 檔案無效") from exc

    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, "input.pptx")
        with open(input_path, "wb") as handle:
            handle.write(pptx_bytes)
        blocks = extract_pptx_blocks(input_path)

    language_summary = detect_document_languages(blocks)
    return {"language_summary": language_summary}


@router.post("/apply")
async def pptx_apply(
    file: UploadFile = File(...),
    blocks: str = Form(...),
    mode: str = Form("bilingual"),
    bilingual_layout: str = Form("inline"),
    fill_color: str | None = Form(None),
    text_color: str | None = Form(None),
    line_color: str | None = Form(None),
    line_dash: str | None = Form(None),
) -> Response:
    valid, error_msg = _validate_file_type(file.filename)
    if not valid:
        raise HTTPException(status_code=400, detail=error_msg)
    try:
        pptx_bytes = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="PPTX 檔案無效") from exc

    try:
        blocks_data = coerce_blocks(json.loads(blocks))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="blocks JSON 無效") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail="blocks 資料無效") from exc

    if mode not in {"bilingual", "correction", "translated"}:
        raise HTTPException(status_code=400, detail="不支援的 mode")
    if mode == "bilingual" and bilingual_layout not in {"inline", "auto", "new_slide"}:
        raise HTTPException(status_code=400, detail="不支援的 bilingual layout")

    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, "input.pptx")
        output_path = os.path.join(temp_dir, "output.pptx")
        with open(input_path, "wb") as handle:
            handle.write(pptx_bytes)

        if mode == "bilingual":
            apply_bilingual(input_path, output_path, blocks_data, layout=bilingual_layout)
        elif mode == "translated":
            apply_translations(input_path, output_path, blocks_data, mode="direct")
        else:
            apply_chinese_corrections(
                input_path,
                output_path,
                blocks_data,
                fill_color=fill_color,
                text_color=text_color,
                line_color=line_color,
                line_dash=line_dash,
            )

        with open(output_path, "rb") as handle:
            output_bytes = handle.read()

    return Response(
        content=output_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": "attachment; filename=output.pptx"},
    )


@router.post("/translate")
async def pptx_translate(
    blocks: str = Form(...),
    source_language: str | None = Form(None),
    secondary_language: str | None = Form(None),
    target_language: str | None = Form(None),
    mode: str = Form("bilingual"),
    use_tm: bool = Form(False),
    provider: str | None = Form(None),
    model: str | None = Form(None),
    api_key: str | None = Form(None),
    base_url: str | None = Form(None),
    ollama_fast_mode: bool = Form(False),
) -> dict:
    llm_mode = os.getenv("TRANSLATE_LLM_MODE", "real").lower()
    try:
        blocks_data = coerce_blocks(json.loads(blocks))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="blocks JSON 無效") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail="blocks 資料無效") from exc

    if not target_language:
        raise HTTPException(status_code=400, detail="target_language 為必填")

    def _prepare_blocks_for_correction(items: list[dict]) -> list[dict]:
        if not source_language or source_language == "auto":
            return items
        prepared = []
        for block in items:
            text = block.get("source_text", "")
            if not text:
                prepared.append(block)
                continue
            lines = []
            for line in text.splitlines():
                lang = detect_language(line)
                if lang == source_language:
                    lines.append(line)
            prepared_block = dict(block)
            prepared_block["source_text"] = "\n".join(lines)
            prepared.append(prepared_block)
        return prepared

    resolved_source_language = resolve_source_language(blocks_data, source_language)

    @contextmanager
    def _temporary_env(updates: dict[str, str]):
        previous = {}
        for key, value in updates.items():
            previous[key] = os.environ.get(key)
            os.environ[key] = value
        try:
            yield
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    env_updates: dict[str, str] = {}
    if resolved_source_language:
        env_updates["SOURCE_LANGUAGE"] = resolved_source_language
    if (provider or "").lower() == "ollama" and ollama_fast_mode:
        env_updates["LLM_SINGLE_REQUEST"] = "0"
        env_updates["LLM_CHUNK_SIZE"] = "1"
        env_updates["LLM_CHUNK_DELAY"] = "0"

    try:
        with _temporary_env(env_updates):
            translated = translate_pptx_blocks(
                _prepare_blocks_for_correction(blocks_data)
                if mode == "correction"
                else blocks_data,
                target_language,
                use_tm=use_tm,
                provider=provider,
                model=model,
                api_key=api_key,
                base_url=base_url,
            )
    except Exception as exc:
        if provider == "ollama" and is_connection_refused(exc):
            raise HTTPException(
                status_code=400,
                detail=build_connection_refused_message(
                    "Ollama", base_url or "http://localhost:11434"
                ),
            ) from exc
        error_msg = str(exc)
        if "image" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail=(
                    "翻譯失敗：偵測到圖片相關錯誤。您的 PPTX 可能包含圖片，"
                    "目前所選模型不支援圖片輸入。請在 LLM 設定中改用支援視覺模型"
                    "（例如 GPT-4o）。"
                ),
            ) from exc
        raise HTTPException(status_code=400, detail=error_msg) from exc
    return {
        "mode": mode,
        "source_language": resolved_source_language or source_language,
        "target_language": target_language,
        "blocks": translated.get("blocks", []),
        "llm_mode": llm_mode,
        "warning": "目前為 mock 模式，翻譯結果會回填原文。" if llm_mode == "mock" else None,
    }
