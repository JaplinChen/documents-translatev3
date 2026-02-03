import logging
import os
from functools import lru_cache

import numpy as np
from typing import TYPE_CHECKING

LOGGER = logging.getLogger(__name__)
if TYPE_CHECKING:
    from paddleocr import PaddleOCR


def map_paddle_lang(tesseract_lang: str) -> str:
    lang = (tesseract_lang or "").lower()
    if "chi_tra" in lang or "chi_sim" in lang or "zh" in lang:
        return "ch"
    if "vie" in lang or "vi" in lang:
        return "vi"
    return "en"


@lru_cache(maxsize=4)
def get_ocr(lang: str) -> "PaddleOCR":
    os.environ.setdefault("FLAGS_use_mkldnn", "0")
    os.environ.setdefault("FLAGS_enable_onednn", "0")
    try:
        import paddle  # noqa: F401
        from paddleocr import PaddleOCR
    except Exception as exc:
        LOGGER.warning("PaddleOCR unavailable: %s", exc)
        raise

    use_angle = os.getenv("PADDLE_OCR_USE_ANGLE", "1").strip() == "1"

    return PaddleOCR(use_angle_cls=use_angle, lang=lang)


def ocr_image(image, tesseract_lang: str) -> list[dict]:
    lang = map_paddle_lang(tesseract_lang)
    ocr = get_ocr(lang)
    result = ocr.ocr(np.array(image))
    lines = []
    if not result:
        return lines
    for line in result[0]:
        if not line or len(line) < 2:
            continue
        points, data = line
        text = data[0] if data else ""
        score = data[1] if data and len(data) > 1 else 0
        if not text:
            continue
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        lines.append(
            {
                "text": text,
                "score": score,
                "x0": min(xs),
                "y0": min(ys),
                "x1": max(xs),
                "y1": max(ys),
            }
        )
    return lines
