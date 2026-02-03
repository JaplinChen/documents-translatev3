from __future__ import annotations

from pydantic import BaseModel


class TermLanguageInput(BaseModel):
    lang_code: str
    value: str | None = None


class TermPayload(BaseModel):
    term: str
    category_id: int | None = None
    category_name: str | None = None
    status: str = "active"
    case_rule: str | None = None
    note: str | None = None
    source: str | None = None
    filename: str | None = None
    aliases: list[str] = []
    languages: list[TermLanguageInput] = []
    created_by: str | None = None
    source_lang: str | None = None
    target_lang: str | None = None
    priority: int | None = 0


class CategoryPayload(BaseModel):
    name: str
    sort_order: int | None = None


class BatchPayload(BaseModel):
    ids: list[int]
    category_id: int | None = None
    status: str | None = None
    case_rule: str | None = None
    source: str | None = None
    priority: int | None = None


class ImportMappingPayload(BaseModel):
    mapping: dict[str, str]
    create_missing_category: bool = True
