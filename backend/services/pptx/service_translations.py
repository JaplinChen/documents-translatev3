from __future__ import annotations

from collections.abc import Iterable

from pptx import Presentation

from .apply_core import _apply_translations_to_presentation
from backend.services.image_replace import replace_images_in_package
import os

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
