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
    is_decorative_block,
    is_garbage_text,
    is_numeric_only,
    is_technical_terms_only,
)
from backend.services.pdf.clustering import cluster_blocks
from backend.services.pdf.ocr_engine import (
    enhance_image_for_ocr,
    get_ocr_config,
    get_poppler_path,
    perform_paddle_ocr_on_page,
)
from backend.services.pdf.table_extract import extract_table_blocks, get_table_config
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
            enhance_image_for_ocr(image),
            output_type=pytesseract.Output.DICT,
            lang=cfg["lang"],
            config=f"--oem {cfg['oem']} --psm {cfg['psm']} -c preserve_interword_spaces={cfg['preserve_interword_spaces']}",
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
    if pdfplumber:
        try:
            plumber_doc = pdfplumber.open(pdf_path)
        except Exception:
            plumber_doc = None
    else:
        plumber_doc = None
    blocks, cfg = [], get_ocr_config()
    sw, sh = 0, 0
    doc_primary_lang = preferred_lang or None

    for page_index, page in enumerate(doc):
        text_dict = page.get_text("dict")
        page_blocks = []

        # 1. Detect Tables First for Spatial Filtering
        table_areas = []
        if plumber_doc and page_index < len(plumber_doc.pages):
            try:
                tables = plumber_doc.pages[page_index].find_tables(table_settings=get_table_config())
                table_areas = [t.bbox for t in tables if getattr(t, "bbox", None)]
                if table_areas:
                    LOGGER.info("Page %s: Detected %s table areas: %s", page_index + 1, len(table_areas), table_areas)
            except Exception as e:
                LOGGER.warning("Spatial table detection failed for page %s: %s", page_index + 1, e)

        def is_in_table(bbox):
            x0, y0, x1, y1 = bbox
            for tx0, ty0, tx1, ty1 in table_areas:
                # Check if center of block is inside table area (more robust)
                cx = (x0 + x1) / 2
                cy = (y0 + y1) / 2
                if tx0 <= cx <= tx1 and ty0 <= cy <= ty1:
                    return True
            return False

        # 2. Standard text extraction — split by line for paragraph granularity
        line_id = 0
        extracted_line_count = 0
        for b_idx, b in enumerate(text_dict["blocks"]):
            if b.get("type") != 0:
                continue

            block_bbox = b.get("bbox")
            # Don't pre-filter. We prefer to deduplicate after we know if table extraction succeeded.
            # Only skip if it's explicitly marked as a non-text block by PyMuPDF (unlikely here)
            if False: # Placeholder for potential future logic
                continue

            for line in b.get("lines", []):
                line_text = "".join(
                    span.get("text", "") for span in line.get("spans", [])
                ).strip()
                if not line_text:
                    continue

                line_id += 1
                extracted_line_count += 1
                line_bbox = line.get("bbox", block_bbox)
                lx0, ly0, lx1, ly1 = line_bbox
                first_span = line["spans"][0] if line.get("spans") else {}
                block = make_block(
                    slide_index=page_index,
                    shape_id=b_idx * 100 + line_id,
                    block_type="pdf_text_block",
                    source_text=line_text,
                    x=lx0,
                    y=ly0,
                    width=lx1 - lx0,
                    height=ly1 - ly0,
                )
                block.update(
                    {
                        "font_size": first_span.get("size", 10.0),
                        "font_name": first_span.get("font", "helv"),
                        "page_no": page_index + 1,
                    }
                )
                page_blocks.append(block)

        # 3. Table extraction
        if plumber_doc and page_index < len(plumber_doc.pages):
            force_ocr = len(page_blocks) == 0
            page_image = None
            need_table_image = os.getenv("PDF_TABLE_LINE_DETECT", "1").strip() == "1"
            if force_ocr or need_table_image:
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
            # Deduplicate: preferring table blocks over standard lines
            final_page_blocks = []
            standard_lines = [b for b in page_blocks if not b.get("is_table")]
            
            # For each standard line, check if it's "covered" by a table cell
            for sl in standard_lines:
                s_x0, s_y0, s_w, s_h = sl["x"], sl["y"], sl["width"], sl["height"]
                scx, scy = s_x0 + s_w/2, s_y0 + s_h/2
                
                is_covered = False
                for tb in table_blocks:
                    tx0, ty0, tw, th = tb["x"], tb["y"], tb["width"], tb["height"]
                    if tx0 <= scx <= tx0 + tw and ty0 <= scy <= ty0 + th:
                        is_covered = True
                        break
                
                if not is_covered:
                    final_page_blocks.append(sl)
            
            final_page_blocks.extend(table_blocks)
            page_blocks = final_page_blocks

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
    # Filter decorative blocks (logo/signature/stamp/watermark)
    if sw and sh:
        blocks = [
            b for b in blocks if not is_decorative_block(b, sw, sh)
        ]
    clustered = cluster_blocks(blocks)

    # Get dimensions for the first page for Slide Preview
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
