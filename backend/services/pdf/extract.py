import logging
import fitz  # PyMuPDF
from pdf2image import convert_from_path
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from backend.contracts import make_block
from backend.services.extract_utils import is_numeric_only, is_technical_terms_only, is_garbage_text
from backend.services.pdf.clustering import cluster_blocks
from backend.services.pdf.ocr_engine import get_ocr_config, get_poppler_path, perform_ocr_on_page, perform_paddle_ocr_on_page
from backend.services.pdf.table_extract import extract_table_blocks

LOGGER = logging.getLogger(__name__)

def extract_blocks(pdf_path: str) -> dict:
    """Extract text blocks from a PDF file using PyMuPDF and optional OCR/Table extraction."""
    doc = fitz.open(pdf_path)
    plumber_doc = pdfplumber.open(pdf_path) if pdfplumber else None
    blocks, cfg = [], get_ocr_config()

    for page_index, page in enumerate(doc):
        text_dict = page.get_text("dict")
        page_blocks = []
        
        # 1. Standard text extraction
        for b_idx, b in enumerate(text_dict["blocks"]):
            if b.get("type") != 0: continue
            text = "".join(span.get("text", "") for line in b.get("lines", []) for span in line.get("spans", [])).strip()
            if not text or is_numeric_only(text) or is_technical_terms_only(text) or is_garbage_text(text): continue
            
            x0, y0, x1, y1 = b.get("bbox")
            first_span = b["lines"][0]["spans"][0] if b["lines"] and b["lines"][0]["spans"] else {}
            block = make_block(page_index, b_idx + 1, "pdf_text_block", text, x0, y0, x1 - x0, y1 - y0)
            block.update({"font_size": first_span.get("size", 10.0), "font_name": first_span.get("font", "helv"), "page_no": page_index + 1})
            page_blocks.append(block)

        # 2. Table extraction if text extraction is sparse or for mixed content
        if plumber_doc and page_index < len(plumber_doc.pages):
            force_ocr = len(page_blocks) == 0
            page_image = None
            if force_ocr:
                try:
                    imgs = convert_from_path(pdf_path, first_page=page_index+1, last_page=page_index+1, dpi=cfg["dpi"], poppler_path=get_poppler_path())
                    page_image = imgs[0] if imgs else None
                except: pass
            
            table_blocks = extract_table_blocks(plumber_doc.pages[page_index], page_index, page_image, cfg, force_ocr)
            existing_texts = {b["source_text"].strip() for b in page_blocks}
            for tb in table_blocks:
                if tb["source_text"].strip() not in existing_texts:
                    page_blocks.append(tb)

        # 3. OCR Fallback if still no blocks
        if not page_blocks:
            ocr_func = perform_paddle_ocr_on_page if cfg.get("engine") == "paddle" else perform_ocr_on_page
            ob, conf = ocr_func(pdf_path, page_index, cfg)
            if cfg.get("engine") != "paddle" and conf < 60 and len(ob) < 5:
                pb, _ = perform_paddle_ocr_on_page(pdf_path, page_index, cfg)
                if len(pb) > len(ob): ob = pb
            page_blocks.extend(ob)

        blocks.extend(page_blocks)

    if plumber_doc: plumber_doc.close()
    clustered = cluster_blocks(blocks)
    LOGGER.info("pdf_extract complete: pages=%s, refined blocks from %s to %s", len(doc), len(blocks), len(clustered))
    return {"blocks": clustered, "page_count": len(doc)}
