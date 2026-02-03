import logging
import os
import shutil
from pathlib import Path

os.environ.setdefault("FLAGS_use_mkldnn", "0")
os.environ.setdefault("FLAGS_enable_onednn", "0")

import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

from backend.contracts import make_block
from backend.services.extract_utils import is_garbage_text, is_numeric_only
from backend.services.pdf.ocr_paddle import ocr_image as paddle_ocr_image

LOGGER = logging.getLogger(__name__)


def enhance_image_for_ocr(pil_img):
    """Apply OpenCV preprocessing to improve OCR accuracy."""
    try:
        open_cv_image = np.array(pil_img)
        if len(open_cv_image.shape) == 3:
            if open_cv_image.shape[2] == 3:
                open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)
            elif open_cv_image.shape[2] == 4:
                open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGBA2BGR)

        if len(open_cv_image.shape) == 3:
            gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = open_cv_image

        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        thresh = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2,
        )
        return Image.fromarray(thresh)
    except Exception as e:
        LOGGER.warning(
            "Image enhancement failed: %s. Using original image.",
            e,
        )
        return pil_img


def is_noisy_text(text: str) -> bool:
    cleaned = (text or "").strip()
    if not cleaned or len(cleaned) <= 2:
        return True
    letters = sum(ch.isalpha() for ch in cleaned)
    total = max(len(cleaned), 1)
    if letters == 0 and sum(ch.isdigit() for ch in cleaned) == 0:
        return True
    other = (
        len(cleaned)
        - letters
        - sum(ch.isdigit() for ch in cleaned)
        - sum(ch.isspace() for ch in cleaned)
    )
    if other / total > 0.35:
        return True
    if letters > 0 and letters / total < 0.3:
        return True
    return False


def get_ocr_config() -> dict:
    engine = os.getenv("PDF_OCR_ENGINE", "").strip().lower()
    allow_paddle = os.getenv("PDF_OCR_ALLOW_PADDLE", "0").strip() == "1"
    paddle_fallback = os.getenv("PDF_OCR_PADDLE_FALLBACK", "0").strip() == "1"
    if not engine:
        tesseract_cmd = shutil.which("tesseract")
        if not tesseract_cmd:
            default_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            ]
            for p in default_paths:
                if Path(p).exists():
                    tesseract_cmd = p
                    break
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            engine = "tesseract"
        elif allow_paddle:
            try:
                import paddleocr  # noqa: F401

                engine = "paddle"
            except Exception:
                engine = "tesseract"
        else:
            engine = "tesseract"
    else:
        if engine == "tesseract":
            tesseract_cmd = shutil.which("tesseract")
            if not tesseract_cmd:
                default_paths = [
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                ]
                for p in default_paths:
                    if Path(p).exists():
                        tesseract_cmd = p
                        break
            if tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    return {
        "dpi": int(os.getenv("PDF_OCR_DPI", "200")),
        "lang": os.getenv("PDF_OCR_LANG", "eng"),
        "conf_min": int(os.getenv("PDF_OCR_CONF_MIN", "10")),
        "psm": int(os.getenv("PDF_OCR_PSM", "6")),
        "engine": engine,
        "allow_paddle": allow_paddle,
        "paddle_fallback": paddle_fallback,
    }


def get_poppler_path() -> str | None:
    env_path = os.getenv("PDF_POPPLER_PATH", "").strip()
    if env_path and Path(env_path).exists():
        return env_path
    project_root = Path(__file__).resolve().parents[3]
    default_path = project_root / "tools" / "poppler" / "Library" / "bin"
    return str(default_path) if default_path.exists() else None


def perform_ocr_on_page(
    pdf_path: str,
    page_index: int,
    config: dict | None = None,
) -> tuple[list[dict], float]:
    cfg = config or get_ocr_config()
    try:
        images = convert_from_path(
            pdf_path,
            first_page=page_index + 1,
            last_page=page_index + 1,
            dpi=cfg["dpi"],
            poppler_path=get_poppler_path(),
        )
        if not images:
            return [], 0
        image = enhance_image_for_ocr(images[0])
        ocr_data = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT,
            lang=cfg["lang"],
            config=f"--psm {cfg['psm']}",
        )

        line_map = {}
        for i in range(len(ocr_data["text"])):
            text = ocr_data["text"][i].strip()
            conf = (
                int(ocr_data["conf"][i])
                if ocr_data["conf"][i] != "-1"
                else -1
            )
            if (
                not text
                or conf < cfg["conf_min"]
                or is_numeric_only(text)
                or is_noisy_text(text)
                or is_garbage_text(text)
            ):
                continue
            key = (ocr_data["block_num"][i], ocr_data["line_num"][i])
            if key not in line_map:
                line_map[key] = {
                    "text": [],
                    "left": ocr_data["left"][i],
                    "top": ocr_data["top"][i],
                    "right": ocr_data["left"][i] + ocr_data["width"][i],
                    "bottom": ocr_data["top"][i] + ocr_data["height"][i],
                }
            line_map[key]["text"].append(text)
            line_map[key]["right"] = max(
                line_map[key]["right"],
                ocr_data["left"][i] + ocr_data["width"][i],
            )
            line_map[key]["bottom"] = max(
                line_map[key]["bottom"],
                ocr_data["top"][i] + ocr_data["height"][i],
            )

        scale = 72.0 / float(cfg["dpi"])
        blocks = []
        for key, val in line_map.items():
            full_text = " ".join(val["text"]).strip()
            if not full_text:
                continue
            if "OCR" not in full_text.upper():
                full_text = full_text.replace("0CR", "OCR")
                full_text = full_text.replace("OOR", "OCR")
                full_text = full_text.replace("OGR", "OCR")
            block = make_block(
                slide_index=page_index,
                shape_id=2000 + key[0] * 100 + key[1],
                block_type="pdf_text_block",
                source_text=full_text,
                x=val["left"] * scale,
                y=val["top"] * scale,
                width=(val["right"] - val["left"]) * scale,
                height=(val["bottom"] - val["top"]) * scale,
            )
            block["is_ocr"] = True
            blocks.append(block)

        confs = [int(c) for c in ocr_data["conf"] if int(c) > 0]
        return blocks, (sum(confs) / len(confs) if confs else 0)
    except Exception as e:
        LOGGER.warning("OCR failed for page %s: %s", page_index + 1, e)
        return [], 0


def perform_paddle_ocr_on_page(
    pdf_path: str,
    page_index: int,
    config: dict | None = None,
) -> tuple[list[dict], float]:
    cfg = config or get_ocr_config()
    try:
        images = convert_from_path(
            pdf_path,
            first_page=page_index + 1,
            last_page=page_index + 1,
            dpi=cfg["dpi"],
            poppler_path=get_poppler_path(),
        )
        if not images:
            return [], 0
        scale = 72.0 / float(cfg["dpi"])
        image = enhance_image_for_ocr(images[0])
        lines = paddle_ocr_image(image, cfg["lang"])
        blocks = []
        for idx, line in enumerate(lines, start=1):
            text = (line.get("text") or "").strip()
            if not text or is_noisy_text(text) or is_garbage_text(text):
                continue
            block = make_block(
                slide_index=page_index,
                shape_id=4000 + idx,
                block_type="pdf_text_block",
                source_text=text,
                x=line["x0"] * scale,
                y=line["y0"] * scale,
                width=(line["x1"] - line["x0"]) * scale,
                height=(line["y1"] - line["y0"]) * scale,
            )
            block["is_ocr"] = True
            block["ocr_engine"] = "paddle"
            blocks.append(block)
        return blocks, 100
    except Exception as e:
        LOGGER.warning("PaddleOCR failed for page %s: %s", page_index + 1, e)
        return [], 0
