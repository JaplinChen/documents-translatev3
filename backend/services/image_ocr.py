from __future__ import annotations

import os
import logging
from io import BytesIO

from PIL import Image
import pytesseract

from backend.services.pdf.ocr_engine import enhance_image_for_ocr, get_ocr_config
from backend.services.pdf.ocr_paddle import (
    is_paddle_gpu_available,
    ocr_image as paddle_ocr_image,
)
from backend.services.extract_utils import (
    is_exact_term_match,
    is_garbage_text,
    is_numeric_only,
    is_symbol_only,
    is_technical_terms_only,
    sanitize_extracted_text,
)
from backend.services.ocr_lang import map_source_lang_to_tesseract

LOGGER = logging.getLogger(__name__)

def _get_image_ocr_lang() -> str:
    env_lang = (os.getenv("IMAGE_OCR_LANG") or "").strip()
    if env_lang and env_lang.lower() != "auto":
        return env_lang
    env_lang = (os.getenv("PDF_OCR_LANG") or "").strip()
    if env_lang and env_lang.lower() != "auto":
        return env_lang
    source_lang = os.getenv("SOURCE_LANGUAGE", "").strip()
    mapped = map_source_lang_to_tesseract(source_lang)
    return mapped or "eng"


def _image_ocr_enabled() -> bool:
    return os.getenv("IMAGE_OCR_ENABLE", "1").strip() == "1"


def _max_pixels() -> int:
    try:
        return int(os.getenv("IMAGE_OCR_MAX_PIXELS", "12000000"))
    except (TypeError, ValueError):
        return 12000000


def _prefer_paddle() -> bool:
    return os.getenv("IMAGE_OCR_PREFER_PADDLE", "0").strip() == "1"


def _image_ocr_engine_override() -> str | None:
    if os.getenv("PDF_OCR_DISABLE_PADDLE", "0").strip() == "1":
        return "tesseract"
    val = os.getenv("IMAGE_OCR_ENGINE", "").strip().lower()
    if val in {"paddle", "tesseract"}:
        return val
    return None


def _resolve_engine(cfg: dict) -> str:
    override = _image_ocr_engine_override()
    if override:
        if override == "paddle" and not is_paddle_gpu_available():
            return "tesseract"
        return override
    if _prefer_paddle():
        try:
            if not is_paddle_gpu_available():
                return "tesseract"
            import paddleocr  # noqa: F401
            import paddle  # noqa: F401

            return "paddle"
        except Exception:
            LOGGER.warning("PaddleOCR not available, falling back to tesseract.")
            return "tesseract"
    return cfg.get("engine", "tesseract")


def _group_tesseract_lines(ocr_data: dict) -> list[dict]:
    lines: dict[tuple[int, int], dict] = {}
    for i in range(len(ocr_data.get("text", []))):
        text = (ocr_data["text"][i] or "").strip()
        if not text:
            continue
        conf_raw = ocr_data["conf"][i]
        try:
            conf = int(conf_raw) if conf_raw != "-1" else -1
        except Exception:
            conf = -1
        key = (ocr_data["block_num"][i], ocr_data["line_num"][i])
        entry = lines.setdefault(
            key,
            {
                "text": [],
                "left": ocr_data["left"][i],
                "top": ocr_data["top"][i],
                "right": ocr_data["left"][i] + ocr_data["width"][i],
                "bottom": ocr_data["top"][i] + ocr_data["height"][i],
                "conf": [],
            },
        )
        entry["text"].append(text)
        entry["conf"].append(conf)
        entry["left"] = min(entry["left"], ocr_data["left"][i])
        entry["top"] = min(entry["top"], ocr_data["top"][i])
        entry["right"] = max(
            entry["right"], ocr_data["left"][i] + ocr_data["width"][i]
        )
        entry["bottom"] = max(
            entry["bottom"], ocr_data["top"][i] + ocr_data["height"][i]
        )
    results = []
    for entry in lines.values():
        results.append(
            {
                "text": " ".join(entry["text"]).strip(),
                "left": entry["left"],
                "top": entry["top"],
                "right": entry["right"],
                "bottom": entry["bottom"],
                "conf": entry["conf"],
            }
        )
    return results


def _ocr_pil_image(image: Image.Image, lang: str, cfg: dict) -> list[dict]:
    engine = _resolve_engine(cfg)
    if engine == "paddle":
        try:
            return [
                {
                    "text": line.get("text", ""),
                    "left": int(line.get("x0", 0)),
                    "top": int(line.get("y0", 0)),
                    "right": int(line.get("x1", 0)),
                    "bottom": int(line.get("y1", 0)),
                    "engine": "paddle",
                }
                for line in paddle_ocr_image(image, lang)
                if line.get("text")
            ]
        except Exception as exc:
            LOGGER.warning("PaddleOCR failed, falling back to tesseract: %s", exc)
            engine = "tesseract"
    enhanced = enhance_image_for_ocr(image)
    ocr_data = pytesseract.image_to_data(
        enhanced,
        lang=lang,
        output_type=pytesseract.Output.DICT,
        config=f"--oem {cfg.get('oem', 1)} --psm {cfg.get('psm', 6)} -c preserve_interword_spaces={cfg.get('preserve_interword_spaces', 1)}",
    )
    lines = []
    for line in _group_tesseract_lines(ocr_data):
        text = sanitize_extracted_text(line.get("text", ""))
        if not text:
            continue
        lines.append(
            {
                "text": text,
                "left": int(line["left"]),
                "top": int(line["top"]),
                "right": int(line["right"]),
                "bottom": int(line["bottom"]),
                "engine": "tesseract",
            }
        )
    return lines


def extract_image_text_blocks(
    image_bytes: bytes,
    slide_index: int,
    shape_id: int | str,
    image_part: str,
    source: str = "pptx",
    ocr_lang: str | None = None,
) -> list[dict]:
    if not _image_ocr_enabled():
        return []

    if not image_bytes:
        return []

    try:
        image = Image.open(BytesIO(image_bytes))
    except Exception:
        return []

    width, height = image.size
    if width * height > _max_pixels():
        return []

    lang = ocr_lang or _get_image_ocr_lang()
    cfg = get_ocr_config()
    blocks: list[dict] = []
    for line in _ocr_pil_image(image, lang, cfg):
        text = sanitize_extracted_text(line.get("text"))
        if (
            not text
            or is_numeric_only(text)
            or is_symbol_only(text)
            or is_exact_term_match(text)
            or is_technical_terms_only(text)
            or is_garbage_text(text)
        ):
            continue
        left = int(line.get("left", 0))
        top = int(line.get("top", 0))
        right = int(line.get("right", 0))
        bottom = int(line.get("bottom", 0))
        blocks.append(
            {
                "slide_index": slide_index,
                "shape_id": shape_id,
                "block_type": "image_text",
                "source_text": text,
                "translated_text": "",
                "x": float(left),
                "y": float(top),
                "width": float(max(0, right - left)),
                "height": float(max(0, bottom - top)),
                "image_part": image_part.lstrip("/"),
                "image_width": width,
                "image_height": height,
                "image_left": left,
                "image_top": top,
                "image_right": right,
                "image_bottom": bottom,
                "ocr_engine": line.get("engine", "tesseract"),
                "source": source,
            }
        )
    return blocks


def extract_image_text_blocks_from_pil(
    image: Image.Image,
    page_index: int,
    page_width: float,
    page_height: float,
    source: str = "pdf",
    ocr_lang: str | None = None,
) -> list[dict]:
    if not _image_ocr_enabled():
        return []

    width, height = image.size
    if width * height > _max_pixels():
        return []

    lang = ocr_lang or _get_image_ocr_lang()
    cfg = get_ocr_config()
    blocks: list[dict] = []

    scale_x = page_width / float(width) if width else 1.0
    scale_y = page_height / float(height) if height else 1.0

    for idx, line in enumerate(_ocr_pil_image(image, lang, cfg)):
        text = sanitize_extracted_text(line.get("text"))
        if (
            not text
            or is_numeric_only(text)
            or is_symbol_only(text)
            or is_exact_term_match(text)
            or is_technical_terms_only(text)
            or is_garbage_text(text)
        ):
            continue
        left = int(line.get("left", 0))
        top = int(line.get("top", 0))
        right = int(line.get("right", 0))
        bottom = int(line.get("bottom", 0))
        x = left * scale_x
        y = top * scale_y
        w = max(0, (right - left) * scale_x)
        h = max(0, (bottom - top) * scale_y)
        blocks.append(
            {
                "slide_index": page_index,
                "page": page_index,
                "page_no": page_index + 1,
                "shape_id": f"pdf-image-{page_index}-{idx}",
                "block_type": "image_text",
                "source_text": text,
                "translated_text": "",
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "image_width": width,
                "image_height": height,
                "image_left": left,
                "image_top": top,
                "image_right": right,
                "image_bottom": bottom,
                "ocr_engine": line.get("engine", "tesseract"),
                "source": source,
            }
        )
    return blocks
