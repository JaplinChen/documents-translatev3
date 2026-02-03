import logging
import os
import pytesseract

import fitz  # PyMuPDF
from pdf2image import convert_from_path

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from backend.contracts import make_block
from backend.services.extract_utils import (
    is_exact_term_match,
    is_garbage_text,
    is_numeric_only,
    is_technical_terms_only,
)
from backend.services.pdf.clustering import cluster_blocks
from backend.services.pdf.ocr_engine import get_ocr_config, get_poppler_path, perform_paddle_ocr_on_page
from backend.services.pdf.table_extract import extract_table_blocks
from backend.services.image_ocr import extract_image_text_blocks_from_pil
from backend.services.language_detect import detect_document_languages
from backend.services.ocr_lang import resolve_ocr_lang_from_doc_lang

LOGGER = logging.getLogger(__name__)


def perform_ocr_on_page(pdf_path: str, page_index: int, config: dict | None = None) -> list[dict]:
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
            return []
        image = images[0]
        ocr_data = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT,
            lang=cfg["lang"],
            config=f"--psm {cfg['psm']}",
        )

        line_map = {}
        for i in range(len(ocr_data["text"])):
            text = ocr_data["text"][i].strip()
            conf = int(ocr_data["conf"][i]) if ocr_data["conf"][i] != "-1" else -1
            if not text or conf < cfg["conf_min"] or is_numeric_only(text) or is_garbage_text(text):
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
    except Exception as e:
        LOGGER.warning("OCR failed for page %s: %s", page_index + 1, e)
        return []


def extract_blocks(pdf_path: str, preferred_lang: str | None = None) -> dict:  # noqa: C901
    """Extract text blocks from PDF using PyMuPDF and OCR/table extraction."""
    doc = fitz.open(pdf_path)
    plumber_doc = pdfplumber.open(pdf_path) if pdfplumber else None
    blocks, cfg = [], get_ocr_config()
    doc_primary_lang = preferred_lang or None

    for page_index, page in enumerate(doc):
        text_dict = page.get_text("dict")
        page_blocks = []

        # 1. Standard text extraction
        for b_idx, b in enumerate(text_dict["blocks"]):
            if b.get("type") != 0:
                continue
            text = "".join(
                span.get("text", "")
                for line in b.get("lines", [])
                for span in line.get("spans", [])
            ).strip()
            if not text or is_garbage_text(text):
                continue

            x0, y0, x1, y1 = b.get("bbox")
            first_span = b["lines"][0]["spans"][0] if b["lines"] and b["lines"][0]["spans"] else {}
            block = make_block(
                slide_index=page_index,
                shape_id=b_idx + 1,
                block_type="pdf_text_block",
                source_text=text,
                x=x0,
                y=y0,
                width=x1 - x0,
                height=y1 - y0,
            )
            block.update(
                {
                    "font_size": first_span.get("size", 10.0),
                    "font_name": first_span.get("font", "helv"),
                    "page_no": page_index + 1,
                }
            )
            page_blocks.append(block)

        # 2. Table extraction if text extraction is sparse or for mixed content
        if plumber_doc and page_index < len(plumber_doc.pages):
            force_ocr = len(page_blocks) == 0
            page_image = None
            if force_ocr:
                try:
                    imgs = convert_from_path(
                        pdf_path,
                        first_page=page_index + 1,
                        last_page=page_index + 1,
                        dpi=cfg["dpi"],
                        poppler_path=get_poppler_path(),
                    )
                    page_image = imgs[0] if imgs else None
                except Exception:
                    pass

            table_blocks = extract_table_blocks(
                plumber_doc.pages[page_index],
                page_index,
                page_image,
                cfg,
                force_ocr,
            )
            existing_texts = {b["source_text"].strip() for b in page_blocks}
            for tb in table_blocks:
                if tb["source_text"].strip() not in existing_texts:
                    page_blocks.append(tb)

        page_lang = None
        if page_blocks and not preferred_lang:
            page_lang = detect_document_languages(page_blocks).get("primary")
            if not doc_primary_lang and page_lang:
                doc_primary_lang = page_lang

        ocr_lang = resolve_ocr_lang_from_doc_lang(page_lang or doc_primary_lang)

        # 3. OCR for image text on page render
        if not page_blocks or os.getenv("IMAGE_OCR_PDF", "1").strip() == "1":
            try:
                imgs = convert_from_path(
                    pdf_path,
                    first_page=page_index + 1,
                    last_page=page_index + 1,
                    dpi=cfg["dpi"],
                    poppler_path=get_poppler_path(),
                )
                page_image = imgs[0] if imgs else None
                if page_image is not None:
                    page_width = page.rect.width
                    page_height = page.rect.height
                    image_blocks = extract_image_text_blocks_from_pil(
                        page_image,
                        page_index=page_index,
                        page_width=page_width,
                        page_height=page_height,
                        source="pdf",
                        ocr_lang=ocr_lang,
                    )
                    page_blocks.extend(image_blocks)
            except Exception:
                pass

        # 4. OCR Fallback if still no blocks
        if not page_blocks:
            ocr_cfg = dict(cfg)
            if ocr_lang:
                ocr_cfg["lang"] = ocr_lang
            ocr_func = (
                perform_paddle_ocr_on_page if ocr_cfg.get("engine") == "paddle" else perform_ocr_on_page
            )
            ocr_result = ocr_func(pdf_path, page_index, ocr_cfg)
            if isinstance(ocr_result, tuple):
                ob, conf = ocr_result
            else:
                ob, conf = ocr_result, 0
            if (
                ocr_cfg.get("paddle_fallback")
                and ocr_cfg.get("engine") != "paddle"
                and conf < 60
                and len(ob) < 5
            ):
                pb, _ = perform_paddle_ocr_on_page(pdf_path, page_index, ocr_cfg)
                if len(pb) > len(ob):
                    ob = pb
            page_blocks.extend(ob)

        blocks.extend(page_blocks)

    if plumber_doc:
        plumber_doc.close()
    for block in blocks:
        block.setdefault("x", 0.0)
        block.setdefault("y", 0.0)
    clustered = cluster_blocks(blocks)

    # Get dimensions for the first page for Slide Preview
    sw, sh = 0, 0
    if len(doc) > 0 and hasattr(doc[0], "rect"):
        rect = doc[0].rect
        sw, sh = rect.width, rect.height

    LOGGER.info(
        "pdf_extract complete: pages=%s, dimensions=%sx%s, refined blocks from %s to %s",
        len(doc),
        sw,
        sh,
        len(blocks),
        len(clustered),
    )
    page_count = len(doc)
    if hasattr(doc, "close"):
        doc.close()
    return {"blocks": clustered, "page_count": page_count, "slide_width": sw, "slide_height": sh}
