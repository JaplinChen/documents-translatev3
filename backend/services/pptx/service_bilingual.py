from __future__ import annotations

from collections.abc import Iterable

from pptx import Presentation
from pptx.dml.color import RGBColor

from backend.services.font_manager import estimate_scale

from .apply_core import _apply_translations_to_presentation
from .apply_layout import add_overflow_textboxes, capture_font_spec
from .apply_shape import find_shape_in_shapes, find_shape_with_id, iter_table_cells
from .apply_slide import duplicate_slide, insert_slide_after
from .apply_text import set_bilingual_text, set_text_preserve_format
from .text_utils import parse_hex_color, split_text_chunks
from .xml_core import get_pptx_theme_summary

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
        return

    theme_data = get_pptx_theme_summary(pptx_in)
    translated_color = _get_translated_color(theme_data)

    table_cell_positions: dict[tuple[int, int], list] = {}
    table_cell_index: dict[tuple[int, int], int] = {}
    supported_types = {"textbox", "table_cell", "notes"}

    for block in blocks:
        if not _should_process_block(block, supported_types):
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
        scale = estimate_scale(source_text, translation)
        block_type = block.get("block_type", "textbox")
        if block_type == "notes":
            _handle_notes_shape(
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
            and _handle_table_cell(
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

        _handle_shape_text(
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


def _apply_new_slide_layout(
    presentation: Presentation,
    blocks: Iterable[dict],
    target_language: str | None,
    font_mapping: dict[str, list[str]] | None,
) -> None:
    slide_blocks: dict[int, list[dict]] = {}
    for block in blocks:
        if not _should_process_block(block, {"textbox"}):
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


def _get_translated_color(
    theme_data: dict[str, dict[str, str]] | None,
) -> RGBColor:
    default = RGBColor(0x1F, 0x77, 0xB4)
    if not theme_data:
        return default
    accent_hex = theme_data.get("colors", {}).get("accent1")
    if not accent_hex:
        return default
    try:
        return parse_hex_color(accent_hex)
    except Exception:
        return default


def _should_process_block(block: dict, supported_types: set[str]) -> bool:
    if block.get("apply") is False or block.get("selected") is False:
        return False
    return block.get("block_type", "textbox") in supported_types


def _handle_notes_shape(
    slide,
    shape_id: int,
    source_text: str,
    translated_text: str,
    combined_text: str,
    layout: str,
    target_language: str | None,
    font_mapping: dict[str, list[str]] | None,
    theme_data: dict[str, dict[str, str]] | None,
    scale: float,
) -> None:
    if not slide.has_notes_slide:
        return
    notes_shape = find_shape_in_shapes(slide.notes_slide.shapes, shape_id)
    if not notes_shape or not notes_shape.has_text_frame:
        return

    auto_size = layout == "auto"
    success = set_bilingual_text(
        notes_shape.text_frame,
        source_text,
        translated_text,
        auto_size=auto_size,
        scale=scale,
        theme_data=theme_data,
        target_language=target_language,
        font_mapping=font_mapping,
    )
    if not success:
        set_text_preserve_format(
            notes_shape.text_frame,
            combined_text,
            scale=scale,
        )


def _handle_table_cell(
    shape,
    slide_index: int,
    shape_id: int,
    block: dict,
    table_cell_positions: dict[tuple[int, int], list],
    table_cell_index: dict[tuple[int, int], int],
    source_text: str,
    translated_text: str,
    combined_text: str,
    layout: str,
    scale: float,
    theme_data: dict[str, dict[str, str]] | None,
    font_mapping: dict[str, list[str]] | None,
    target_language: str | None,
) -> bool:
    if (
        block.get("block_type") != "table_cell"
        or not getattr(shape, "has_table", False)
    ):
        return False

    key = (slide_index, shape_id)
    if key not in table_cell_positions:
        table_cell_positions[key] = iter_table_cells(shape)
        table_cell_index[key] = 0

    current = table_cell_index[key]
    cells = table_cell_positions[key]
    if current >= len(cells):
        return True

    auto_size = layout == "auto"
    cell_frame = cells[current]
    success = set_bilingual_text(
        cell_frame,
        source_text,
        translated_text,
        auto_size=auto_size,
        scale=scale,
        theme_data=theme_data,
        target_language=target_language,
        font_mapping=font_mapping,
    )
    if not success:
        set_text_preserve_format(
            cell_frame,
            combined_text,
            scale=scale,
        )

    table_cell_index[key] = current + 1
    return True


def _handle_shape_text(
    slide,
    shape,
    layout: str,
    source_text: str,
    translated_text: str,
    combined_text: str,
    scale: float,
    theme_data: dict[str, dict[str, str]] | None,
    target_language: str | None,
    font_mapping: dict[str, list[str]] | None,
    translated_color: RGBColor,
    slide_height: int,
) -> None:
    auto_size = layout == "auto"
    if auto_size and len(translated_text) > 400:
        set_text_preserve_format(shape.text_frame, source_text)
        chunks = split_text_chunks(translated_text, 300)
        add_overflow_textboxes(
            slide,
            shape,
            chunks,
            capture_font_spec(shape.text_frame),
            translated_color,
            slide_height,
        )
        return

    success = set_bilingual_text(
        shape.text_frame,
        source_text,
        translated_text,
        auto_size=auto_size,
        scale=scale,
        theme_data=theme_data,
        target_language=target_language,
        font_mapping=font_mapping,
    )
    if not success:
        set_text_preserve_format(
            shape.text_frame,
            combined_text,
            scale=scale,
        )
