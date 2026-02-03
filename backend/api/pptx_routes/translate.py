from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.config import settings
from backend.services.correction_mode import apply_correction_mode
from backend.services.llm_errors import (
    build_connection_refused_message,
    is_connection_refused,
)
from backend.services.translate_llm import (
    translate_blocks_async as translate_pptx_blocks_async,
)

from .models import TranslateRequest
from .utils import (
    _parse_blocks,
    _prepare_blocks_for_correction,
    _resolve_language,
    _resolve_param_overrides,
)

router = APIRouter()


@router.post("/translate")
async def pptx_translate(
    request: TranslateRequest | None = None,
    **kwargs,
) -> dict:
    """Translate text blocks using LLM."""
    if request is None:
        request = TranslateRequest(**kwargs)
    llm_mode = settings.translate_llm_mode
    blocks = request.blocks
    source_language = request.source_language
    target_language = request.target_language
    mode = request.mode
    use_tm = request.use_tm
    provider = request.provider
    model = request.model
    api_key = request.api_key
    base_url = request.base_url
    ollama_fast_mode = request.ollama_fast_mode
    tone = request.tone
    vision_context = request.vision_context
    smart_layout = request.smart_layout
    refresh = request.refresh
    similarity_threshold = request.similarity_threshold
    scope_type = request.scope_type
    scope_id = request.scope_id
    domain = request.domain
    category = request.category

    blocks_data = _parse_blocks(blocks, "translate")

    if not target_language:
        raise HTTPException(status_code=400, detail="target_language 為必填")

    resolved_source_language = _resolve_language(
        blocks_data,
        source_language,
    )

    param_overrides = _resolve_param_overrides(provider, refresh, ollama_fast_mode)

    try:
        translated = await translate_pptx_blocks_async(
            _prepare_blocks_for_correction(blocks_data, target_language)
            if mode == "correction"
            else blocks_data,
            target_language,
            source_language=resolved_source_language,
            use_tm=use_tm,
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
            tone=tone,
            vision_context=vision_context,
            smart_layout=smart_layout,
            scope_type=scope_type,
            scope_id=scope_id,
            domain=domain,
            category=category,
            param_overrides={**param_overrides, "refresh": refresh},
        )
    except Exception as exc:
        if provider == "ollama" and is_connection_refused(exc):
            raise HTTPException(
                status_code=400,
                detail=build_connection_refused_message(
                    "Ollama",
                    base_url or "http://localhost:11434",
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

    result_blocks = translated.get("blocks", [])
    if mode == "correction":
        translated_texts = [b.get("translated_text", "") for b in result_blocks]
        result_blocks = apply_correction_mode(
            blocks_data,
            translated_texts,
            target_language,
            similarity_threshold=similarity_threshold,
        )

    return {
        "mode": mode,
        "source_language": resolved_source_language or source_language,
        "target_language": target_language,
        "blocks": result_blocks,
        "llm_mode": llm_mode,
        "warning": "目前為 mock 模式，翻譯結果會回填原文。" if llm_mode == "mock" else None,
    }
