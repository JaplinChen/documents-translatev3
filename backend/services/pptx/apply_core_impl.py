from __future__ import annotations

from collections.abc import Iterable

from .apply_core_impl_helpers import (
    apply_table_cell,
    apply_text_frame,
    apply_to_notes,
    build_theme_data,
    compose_text,
    compute_scale,
    optimize_slides,
    reset_shape_geometry,
    resolve_shape,
)


def _apply_translations_to_presentation(
    presentation,
    blocks: Iterable[dict],
    mode: str = "direct",
    target_language: str | None = None,
    font_mapping: dict[str, list[str]] | None = None,
) -> None:
    table_cell_positions: dict[tuple[int, int], list] = {}
    table_cell_index: dict[tuple[int, int], int] = {}

    theme_data, accent_color = build_theme_data(presentation)
    slides_to_optimize: set[int] = set()

    for block in blocks:
        slide_index = block.get("slide_index")
        shape_id = block.get("shape_id")
        if slide_index is None or shape_id is None:
            continue
        if slide_index < 0 or slide_index >= len(presentation.slides):
            continue

        slide = presentation.slides[slide_index]
        scale = compute_scale(block)
        is_auto_layout = block.get("layout", "auto") in {"auto", "new_slide"}
        if block.get("layout") == "new_slide":
            slides_to_optimize.add(slide_index)

        combined_text = compose_text(
            block.get("source_text", ""),
            block.get("translated_text", ""),
            mode,
        )
        block_type = block.get("block_type", "textbox")
        shape = resolve_shape(slide, shape_id, block_type)
        if shape is None:
            continue

        if apply_to_notes(
            shape,
            mode,
            scale,
            target_language,
            font_mapping,
            theme_data,
            is_auto_layout,
            block,
            combined_text,
        ):
            continue

        if apply_table_cell(
            slide,
            shape,
            block,
            table_cell_positions,
            table_cell_index,
            mode,
            scale,
            target_language,
            font_mapping,
            theme_data,
            is_auto_layout,
            combined_text,
        ):
            continue

        if not shape.has_text_frame:
            continue

        orig_geom = (
            shape.left,
            shape.top,
            shape.width,
            shape.height,
        )
        try:
            apply_text_frame(
                slide,
                shape,
                block,
                mode,
                is_auto_layout,
                scale,
                target_language,
                font_mapping,
                theme_data,
                combined_text,
                accent_color,
                presentation.slide_height,
            )
        finally:
            reset_shape_geometry(shape, orig_geom)

    optimize_slides(presentation, slides_to_optimize)
