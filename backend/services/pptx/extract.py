from __future__ import annotations

from pptx import Presentation

from .extract_helpers import emu_to_points
from .extract_iterators import (
    iter_master_blocks,
    iter_notes_blocks,
    iter_table_blocks,
    iter_textbox_blocks,
)


def extract_blocks(pptx_path: str) -> dict:
    presentation = Presentation(pptx_path)
    blocks: list[dict] = []

    slide_width = emu_to_points(presentation.slide_width)
    slide_height = emu_to_points(presentation.slide_height)

    for slide_index, slide in enumerate(presentation.slides):
        seen_ids = set()
        blocks.extend(iter_textbox_blocks(slide, slide_index, seen_ids))
        blocks.extend(iter_table_blocks(slide, slide_index))
        blocks.extend(iter_notes_blocks(slide, slide_index))

    import os

    if os.getenv("PPTX_EXTRACT_MASTERS", "0") == "1":
        blocks.extend(iter_master_blocks(presentation))

    return {
        "blocks": blocks,
        "slide_width": slide_width,
        "slide_height": slide_height,
    }
