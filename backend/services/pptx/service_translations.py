from __future__ import annotations

from collections.abc import Iterable

from pptx import Presentation

from .apply_core import _apply_translations_to_presentation

def apply_translations(
    pptx_in: str,
    pptx_out: str,
    blocks: Iterable[dict],
    mode: str = "direct",
    target_language: str | None = None,
    font_mapping: dict[str, list[str]] | None = None,
) -> None:
    presentation = Presentation(pptx_in)
    presentation._pptx_path = pptx_in
    _apply_translations_to_presentation(
        presentation,
        blocks,
        mode=mode,
        target_language=target_language,
        font_mapping=font_mapping,
    )
    presentation.save(pptx_out)
