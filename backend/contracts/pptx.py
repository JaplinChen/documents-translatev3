from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

class PPTXBlock(BaseModel):
    slide_index: int
    shape_id: Any
    block_type: str  # Use str to be more flexible, but validated in make_block
    source_text: str
    translated_text: str = ""
    client_id: str | None = None
    mode: Literal["direct", "bilingual", "correction"] = "direct"
    # Layout info (in Points)
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    # Style info
    font_size: float | None = None
    font_name: str | None = None

    model_config = ConfigDict(extra="allow")


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
    shape_id: Any,
    block_type: Literal[
        "textbox",
        "table_cell",
        "notes",
        "spreadsheet_cell",
        "pdf_text_block",
        "complex_graphic",
        "master",
    ],
    source_text: str,
    translated_text: str = "",
    mode: Literal["direct", "bilingual", "correction"] = "direct",
    x: float = 0.0,
    y: float = 0.0,
    width: float = 0.0,
    height: float = 0.0,
) -> dict:
    block = PPTXBlock(
        slide_index=slide_index,
        shape_id=shape_id,
        block_type=block_type,
        source_text=source_text,
        translated_text=translated_text,
        mode=mode,
        x=x,
        y=y,
        width=width,
        height=height,
    )
    return _model_dump(block)


def coerce_blocks(blocks: Iterable[dict]) -> list[dict]:
    validated = []
    for block in blocks:
        model = _model_validate(PPTXBlock, block)
        validated.append(_model_dump(model))
    return validated
