from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException

from backend.services.llm_errors import (
    build_connection_refused_message,
    is_connection_refused,
)
from backend.services.llm_models import (
    list_gemini_models,
    list_ollama_models,
    list_openai_models,
)

router = APIRouter(prefix="/api/llm")


@router.post("/models")
async def llm_models(
    provider: str = Form(...),
    api_key: str | None = Form(None),
    base_url: str | None = Form(None),
) -> dict:
    provider = provider.lower()
    try:
        if provider in {"openai", "chatgpt"}:
            if not api_key:
                raise HTTPException(status_code=400, detail="API key 為必填")
            models = list_openai_models(
                api_key,
                base_url or "https://api.openai.com/v1",
            )
        elif provider == "gemini":
            if not api_key:
                raise HTTPException(status_code=400, detail="API key 為必填")
            models = list_gemini_models(
                api_key,
                base_url
                or "https://generativelanguage.googleapis.com/v1beta",
            )
        elif provider == "ollama":
            models = list_ollama_models(
                base_url or "http://host.docker.internal:11434"
            )
        else:
            raise HTTPException(status_code=400, detail="不支援的 provider")
    except HTTPException:
        raise
    except Exception as exc:
        if provider == "ollama" and is_connection_refused(exc):
            raise HTTPException(
                status_code=400,
                detail=build_connection_refused_message(
                    "Ollama",
                    base_url or "http://host.docker.internal:11434",
                ),
            ) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"models": models}
