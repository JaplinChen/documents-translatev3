from __future__ import annotations

from pydantic import BaseModel


class TranslateRequest(BaseModel):
    blocks: str | list[dict]
    source_language: str | None = None
    target_language: str
    secondary_language: str | None = None
    mode: str = "bilingual"
    use_tm: bool = False
    provider: str | None = None
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    ollama_fast_mode: bool = False
    tone: str | None = None
    vision_context: bool = True
    smart_layout: bool = True
    refresh: bool = False
    completed_ids: str | list[str] | list[int] | None = None
    similarity_threshold: float = 0.75
    scope_type: str | None = "project"
    scope_id: str | None = "default"
    domain: str | None = None
    category: str | None = None
