from __future__ import annotations

from pydantic import BaseModel


class GlossaryEntry(BaseModel):
    """
    Glossary entry data structure for translation consistency.
    """

    model_config = {"extra": "ignore"}
    id: int | None = None
    source_lang: str
    target_lang: str
    source_text: str
    target_text: str | None = ""
    priority: int | None = 0
    category_id: int | None = None
    domain: str | None = None
    category: str | None = None
    scope_type: str | None = "project"
    scope_id: str | None = "default"


class GlossaryDelete(BaseModel):
    id: int


class BatchDelete(BaseModel):
    ids: list[int]


class MemoryEntry(BaseModel):
    """
    Translation memory entry for reuse of previous translations.
    """

    model_config = {"extra": "ignore"}
    id: int | None = None
    source_lang: str
    target_lang: str
    source_text: str
    target_text: str | None = ""
    category_id: int | None = None
    domain: str | None = None
    category: str | None = None
    scope_type: str | None = "project"
    scope_id: str | None = "default"


class MemoryDelete(BaseModel):
    id: int


class CategoryPayload(BaseModel):
    name: str
    sort_order: int | None = 0


class GlossaryExtractPayload(BaseModel):
    blocks: list[dict]
    target_language: str = "zh-TW"
    provider: str | None = None
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None


class TermFeedbackPayload(BaseModel):
    source: str
    target: str
    source_lang: str | None = None
    target_lang: str | None = "zh-TW"
