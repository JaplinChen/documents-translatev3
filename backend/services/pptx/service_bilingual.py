from __future__ import annotations

from collections.abc import Iterable

from pptx import Presentation

from .apply_core import _apply_translations_to_presentation
from .apply_shape import find_shape_with_id
from .apply_slide import duplicate_slide, insert_slide_after
from .text_utils import split_text_chunks
from .xml_core import get_pptx_theme_summary
from .service_bilingual_helpers import (
    compute_scale,
    get_translated_color,
    handle_notes_shape,
    handle_shape_text,
    handle_table_cell,
    should_process_block,
)
from backend.services.image_replace import replace_images_in_package
import os


def apply_bilingual(  # noqa: C901
    pptx_in: str,
    pptx_out: str,
    blocks: list[dict],
    layout: str = "inline",
    target_language: str | None = None,
    font_mapping: dict[str, list[str]] | None = None,
) -> None:
    presentation = Presentation(pptx_in)
    presentation._pptx_path = pptx_in

    if layout == "new_slide":
        _apply_new_slide_layout(
            presentation,
            blocks,
            target_language=target_language,
            font_mapping=font_mapping,
        )
        presentation.save(pptx_out)
        tmp_out = f"{pptx_out}.imgtmp"
        try:
            did_replace = replace_images_in_package(pptx_out, tmp_out, blocks)
            if did_replace and os.path.exists(tmp_out):
                os.replace(tmp_out, pptx_out)
        finally:
            if os.path.exists(tmp_out):
                try:
                    os.remove(tmp_out)
                except Exception:
                    pass
        return

    theme_data = get_pptx_theme_summary(pptx_in)
    translated_color = get_translated_color(theme_data)

    table_cell_positions: dict[tuple[int, int], list] = {}
    table_cell_index: dict[tuple[int, int], int] = {}
    supported_types = {"textbox", "table_cell", "notes"}

    for block in blocks:
        if not should_process_block(block, supported_types):
            continue
        translation = block.get("translated_text", "")
        if not translation:
            continue
        slide_index = block.get("slide_index")
        shape_id = block.get("shape_id")
        if slide_index is None or shape_id is None:
            continue
        if slide_index >= len(presentation.slides):
            continue

        slide = presentation.slides[slide_index]
        source_text = block.get("source_text", "")
        target_lang = block.get("target_language") or target_language
        combined_text = f"{source_text}\n\n{translation}"
        scale = compute_scale(source_text, translation)
        block_type = block.get("block_type", "textbox")
        if block_type == "notes":
            handle_notes_shape(
                slide,
                shape_id,
                source_text,
                translation,
                combined_text,
                layout,
                target_lang,
                font_mapping,
                theme_data,
                scale,
            )
            continue

        shape = find_shape_with_id(slide, shape_id)
        if not shape:
            continue

        if (
            block_type == "table_cell"
            and getattr(shape, "has_table", False)
            and handle_table_cell(
                shape,
                slide_index,
                shape_id,
                block,
                table_cell_positions,
                table_cell_index,
                source_text,
                translation,
                combined_text,
                layout,
                scale,
                theme_data,
                font_mapping,
                target_language,
            )
        ):
            continue

        if not shape.has_text_frame:
            continue

        handle_shape_text(
            slide,
            shape,
            layout,
            source_text,
            translation,
            combined_text,
            scale,
            theme_data,
            target_language,
            font_mapping,
            translated_color,
            presentation.slide_height,
        )

    presentation.save(pptx_out)
    tmp_out = f"{pptx_out}.imgtmp"
    try:
        did_replace = replace_images_in_package(pptx_out, tmp_out, blocks)
        if did_replace and os.path.exists(tmp_out):
            os.replace(tmp_out, pptx_out)
    finally:
        if os.path.exists(tmp_out):
            try:
                os.remove(tmp_out)
            except Exception:
                pass


def _apply_new_slide_layout(
    presentation: Presentation,
    blocks: Iterable[dict],
    target_language: str | None,
    font_mapping: dict[str, list[str]] | None,
) -> None:
    slide_blocks: dict[int, list[dict]] = {}
    for block in blocks:
        if not should_process_block(block, {"textbox"}):
            continue
        slide_index = block.get("slide_index")
        if slide_index is None:
            continue
        slide_blocks.setdefault(slide_index, []).append(block)

    new_blocks: list[dict] = []
    offset = 0
    for slide_index in range(len(presentation.slides)):
        if slide_index not in slide_blocks:
            continue
        source_slide = presentation.slides[slide_index + offset]
        try:
            new_slide, shape_map = duplicate_slide(presentation, source_slide)
        except Exception:  # pragma: no cover
            new_slide = presentation.slides.add_slide(
                presentation.slide_layouts[6]
            )
            shape_map = {}

        insert_slide_after(presentation, new_slide, slide_index + offset)
        offset += 1
        new_slide_index = slide_index + offset
        for block in slide_blocks[slide_index]:
            updated = dict(block)
            updated["slide_index"] = new_slide_index
            updated["layout"] = "new_slide"
            old_sid = updated.get("shape_id")
            if old_sid in shape_map:
                updated["shape_id"] = shape_map[old_sid]
            new_blocks.append(updated)

    _apply_translations_to_presentation(
        presentation,
        new_blocks,
        mode="direct",
        target_language=target_language,
        font_mapping=font_mapping,
    )
