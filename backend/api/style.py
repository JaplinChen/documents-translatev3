import json

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/style")


class StyleSuggestRequest(BaseModel):
    blocks: list[dict]
    provider: str | None = None
    model: str | None = None


@router.post("/suggest")
async def suggest_style(request: StyleSuggestRequest):
    # 1. Extract context
    texts = [
        b.get("source_text", "")
        for b in request.blocks[:10]
    ]  # Take first 10 blocks for context
    context = "\n".join(texts)

    if not context.strip():
        # Default theme if no text
        return {
            "theme_name": "Modern Business",
            "primary_color": "#2C3E50",
            "secondary_color": "#E74C3C",
            "accent_color": "#3498DB",
            "font_recommendation": "Inter",
            "rationale": "Default professional theme.",
        }

    # 2. Call LLM
    from backend.services.prompt_store import render_prompt

    prompt = render_prompt("style_suggestion", {"context": context})

    try:
        # For POC, we'll use a mocked structure if LLM is not configured,
        # but here we try to use the system's llm infrastructure.
        from backend.services.llm_clients import get_client

        # Defaulting to a safe model if not provided
        client = get_client(request.provider or "openai", request.model)
        response_text = await client.generate(prompt)

        # Clean response text from markdown code blocks
        clean_json = (
            response_text.replace("```json", "")
            .replace("```", "")
            .strip()
        )
        return json.loads(clean_json)
    except Exception:
        # Fallback to a smart default if LLM fails
        return {
            "theme_name": "Analyzed AI Theme",
            "primary_color": "#1A1A1B",
            "secondary_color": "#3B82F6",
            "accent_color": "#10B981",
            "font_recommendation": "Outfit",
            "rationale": "Calculated based on document structure (fallback).",
        }
