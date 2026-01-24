import logging
import os
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path

from backend.contracts import make_block
from backend.services.extract_utils import is_numeric_only, is_technical_terms_only

LOGGER = logging.getLogger(__name__)


def get_ocr_config() -> dict:
    try:
        dpi = int(os.getenv("PDF_OCR_DPI", "200"))
    except ValueError:
        dpi = 200

    lang = os.getenv("PDF_OCR_LANG", "eng")

    try:
        conf_min = int(os.getenv("PDF_OCR_CONF_MIN", "10"))
    except ValueError:
        conf_min = 10

    return {"dpi": dpi, "lang": lang, "conf_min": conf_min}


def perform_ocr_on_page(pdf_path: str, page_index: int, config: dict | None = None) -> list[dict]:
    """
    Use pdf2image and pytesseract to extract text from a specific PDF page.
    """
    cfg = config or get_ocr_config()
    dpi = cfg["dpi"]
    lang = cfg["lang"]
    conf_min = cfg["conf_min"]

    try:
        images = convert_from_path(pdf_path, first_page=page_index + 1, last_page=page_index + 1, dpi=dpi)
        if not images:
            return []

        image = images[0]
        ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, lang=lang)

        blocks = []
        n_boxes = len(ocr_data["text"])

        line_map = {}

        for i in range(n_boxes):
            text = ocr_data["text"][i].strip()
            try:
                conf = int(ocr_data["conf"][i])
            except ValueError:
                conf = -1

            if not text or conf < conf_min:
                continue

            if is_numeric_only(text):
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
            line_map[key]["left"] = min(line_map[key]["left"], ocr_data["left"][i])
            line_map[key]["top"] = min(line_map[key]["top"], ocr_data["top"][i])
            line_map[key]["right"] = max(line_map[key]["right"], ocr_data["left"][i] + ocr_data["width"][i])
            line_map[key]["bottom"] = max(line_map[key]["bottom"], ocr_data["top"][i] + ocr_data["height"][i])

        scale = 72.0 / float(dpi)

        for key, val in line_map.items():
            full_text = " ".join(val["text"]).strip()
            if not full_text:
                continue

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

        return blocks
    except Exception as exc:
        LOGGER.warning("OCR failed for page %s: %s", page_index + 1, exc)
        return []


def extract_blocks(pdf_path: str) -> dict:
    """
    Extract text blocks from a PDF file using PyMuPDF.

    Returns blocks with coordinate information for side-by-side or overlay.
    """
    doc = fitz.open(pdf_path)
    blocks: list[dict] = []
    cfg = get_ocr_config()

    for page_index, page in enumerate(doc):
        block_id_counter = 0
        text_dict = page.get_text("dict")

        has_images = any(b.get("type") == 1 for b in text_dict["blocks"])

        current_page_blocks = []
        for b in text_dict["blocks"]:
            if b.get("type") != 0:
                continue

            lines = b.get("lines", [])
            if not lines:
                continue

            block_text = ""
            first_span = lines[0]["spans"][0] if lines[0]["spans"] else {}
            font_size = first_span.get("size", 10.0)
            font_name = first_span.get("font", "helv")

            for line in lines:
                for span in line.get("spans", []):
                    block_text += span.get("text", "")

            text = block_text.strip()
            if not text or is_numeric_only(text) or is_technical_terms_only(text):
                continue

            block_id_counter += 1
            x0, y0, x1, y1 = b.get("bbox")

            block = make_block(
                slide_index=page_index,
                shape_id=block_id_counter,
                block_type="pdf_text_block",
                source_text=text,
                x=x0,
                y=y0,
                width=x1 - x0,
                height=y1 - y0,
            )
            block.update(
                {
                    "font_size": font_size,
                    "font_name": font_name,
                    "page_no": page_index + 1,
                    "block_no": b.get("number", 0),
                }
            )
            current_page_blocks.append(block)

        ocr_blocks = []
        if not current_page_blocks:
            ocr_blocks = perform_ocr_on_page(pdf_path, page_index, cfg)
            current_page_blocks.extend(ocr_blocks)

        LOGGER.info(
            "pdf_extract page=%s text_blocks=%s ocr_blocks=%s has_images=%s",
            page_index + 1,
            len(current_page_blocks) - len(ocr_blocks),
            len(ocr_blocks),
            has_images,
        )

        blocks.extend(current_page_blocks)

    LOGGER.info("pdf_extract complete pages=%s blocks=%s", len(doc), len(blocks))

    return {"blocks": blocks, "page_count": len(doc)}
