from __future__ import annotations

from typing import Any, Iterable, Literal

from pydantic import BaseModel


class PPTXBlock(BaseModel):
    slide_index: int
    shape_id: int
    block_type: Literal["textbox", "table_cell", "notes"]
    source_text: str
    translated_text: str = ""
    mode: Literal["direct", "bilingual", "correction"] = "direct"


class PPTXExtractResponse(BaseModel):
    blocks: list[PPTXBlock]


def _model_dump(model: BaseModel) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _model_validate(model_cls, data: dict) -> BaseModel:
    if hasattr(model_cls, "model_validate"):
        return model_cls.model_validate(data)
    return model_cls.parse_obj(data)


def make_block(
    slide_index: int,
    shape_id: int,
    block_type: Literal["textbox", "table_cell", "notes"],
    source_text: str,
    translated_text: str = "",
    mode: Literal["direct", "bilingual", "correction"] = "direct",
) -> dict:
    block = PPTXBlock(
        slide_index=slide_index,
        shape_id=shape_id,
        block_type=block_type,
        source_text=source_text,
        translated_text=translated_text,
        mode=mode,
    )
    return _model_dump(block)


def coerce_blocks(blocks: Iterable[dict]) -> list[dict]:
    validated = []
    for block in blocks:
        model = _model_validate(PPTXBlock, block)
        validated.append(_model_dump(model))
    return validated
