from __future__ import annotations

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from .extract_helpers import emu_to_points, iter_shapes
from .extract_iterators import (
    iter_master_blocks,
    iter_notes_blocks,
    iter_table_blocks,
    iter_textbox_blocks,
)
from backend.services.image_ocr import extract_image_text_blocks
from backend.services.language_detect import detect_document_languages
from backend.services.ocr_lang import resolve_ocr_lang_from_doc_lang


def extract_blocks(pptx_path: str, preferred_lang: str | None = None) -> dict:
    presentation = Presentation(pptx_path)
    blocks: list[dict] = []
    image_jobs: list[dict] = []

    slide_width = emu_to_points(presentation.slide_width)
    slide_height = emu_to_points(presentation.slide_height)

    for slide_index, slide in enumerate(presentation.slides):
        seen_ids = set()
        blocks.extend(iter_textbox_blocks(slide, slide_index, seen_ids))
        blocks.extend(iter_table_blocks(slide, slide_index))
        blocks.extend(iter_notes_blocks(slide, slide_index))
        for shape in iter_shapes(slide.shapes):
            try:
                if shape.shape_type != MSO_SHAPE_TYPE.PICTURE:
                    continue
                image_bytes = None
                image_part = None
                if getattr(shape, "image", None) is not None:
                    try:
                        image_bytes = shape.image.blob
                        image_part = str(shape.image.partname)
                    except Exception:
                        image_bytes = None
                        image_part = None
                if image_bytes is None:
                    r_id = shape._element.blipFill.blip.embed  # noqa: SLF001
                    part = slide.part.related_parts.get(r_id)
                    if not part:
                        continue
                    image_part = str(part.partname)
                    image_bytes = part.blob

                image_jobs.append(
                    {
                        "image_bytes": image_bytes,
                        "slide_index": slide_index,
                        "shape_id": getattr(shape, "shape_id", None) or image_part or slide_index,
                        "image_part": image_part,
                        "shape_left": shape.left,
                        "shape_top": shape.top,
                        "shape_width": shape.width,
                        "shape_height": shape.height,
                    }
                )
            except Exception:
                continue

    import os
    import zipfile

    doc_lang = preferred_lang or (detect_document_languages(blocks).get("primary") if blocks else None)
    ocr_lang = resolve_ocr_lang_from_doc_lang(doc_lang)

    for job in image_jobs:
        image_blocks = extract_image_text_blocks(
            job["image_bytes"],
            slide_index=job["slide_index"],
            shape_id=job["shape_id"],
            image_part=job["image_part"],
            source="pptx",
            ocr_lang=ocr_lang,
        )
        if image_blocks:
            slide_left = emu_to_points(job["shape_left"])
            slide_top = emu_to_points(job["shape_top"])
            slide_w = emu_to_points(job["shape_width"])
            slide_h = emu_to_points(job["shape_height"])
            img_w = image_blocks[0].get("image_width") or 1
            img_h = image_blocks[0].get("image_height") or 1
            scale_x = slide_w / float(img_w)
            scale_y = slide_h / float(img_h)
            for block in image_blocks:
                block["x"] = slide_left + block["x"] * scale_x
                block["y"] = slide_top + block["y"] * scale_y
                block["width"] = block["width"] * scale_x
                block["height"] = block["height"] * scale_y
            blocks.extend(image_blocks)

    if os.getenv("PPTX_EXTRACT_MASTERS", "0") == "1":
        blocks.extend(iter_master_blocks(presentation))

    # Fallback: scan media parts directly (covers floating/unsupported image refs)
    try:
        with zipfile.ZipFile(pptx_path, "r") as zf:
            media_files = [n for n in zf.namelist() if n.startswith("ppt/media/")]
            for idx, name in enumerate(media_files):
                try:
                    image_bytes = zf.read(name)
                except Exception:
                    continue
                blocks.extend(
                    extract_image_text_blocks(
                        image_bytes,
                        slide_index=-1,
                        shape_id=f"pptx-image-{idx}",
                        image_part=name,
                        source="pptx",
                        ocr_lang=ocr_lang,
                    )
                )
    except Exception:
        pass

    return {
        "blocks": blocks,
        "slide_width": slide_width,
        "slide_height": slide_height,
    }
