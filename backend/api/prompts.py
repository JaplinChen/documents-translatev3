from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException

from backend.services.prompt_store import get_prompt, list_prompts, save_prompt

router = APIRouter(prefix="/api/prompts")


@router.get("")
async def prompt_list() -> list[str]:
    return list_prompts()


@router.get("/{name}")
async def prompt_get(name: str) -> dict:
    try:
        content = get_prompt(name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"name": name, "content": content}


@router.post("/{name}")
async def prompt_save(name: str, content: str = Body(..., embed=True)) -> dict:
    save_prompt(name, content)
    return {"status": "ok"}
