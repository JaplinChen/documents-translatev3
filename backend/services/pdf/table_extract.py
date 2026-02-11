import logging
import os

import pytesseract
import cv2
import numpy as np

from backend.contracts import make_block
from backend.services.extract_utils import (
    is_garbage_text,
    is_numeric_only,
    is_technical_terms_only,
)
from backend.services.pdf.ocr_engine import (
    enhance_image_for_ocr,
    is_noisy_text,
    paddle_ocr_image,
)

LOGGER = logging.getLogger(__name__)


def _cluster_positions(values: list[int], tol: int) -> list[int]:
    if not values:
        return []
    values = sorted(values)
    clusters = [[values[0]]]
    for v in values[1:]:
        if abs(v - clusters[-1][-1]) <= tol:
            clusters[-1].append(v)
        else:
            clusters.append([v])
    return [int(sum(c) / len(c)) for c in clusters]


def _detect_table_grid_lines(
    image,
    min_len: int,
) -> tuple[list[int], list[int]]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    bw = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        15,
        2,
    )

    h_kernel = max(10, image.shape[1] // 30)
    v_kernel = max(10, image.shape[0] // 30)

    horizontal = cv2.morphologyEx(
        bw,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (h_kernel, 1)),
        iterations=1,
    )
    vertical = cv2.morphologyEx(
        bw,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_kernel)),
        iterations=1,
    )

    x_positions = []
    y_positions = []

    contours, _ = cv2.findContours(
        horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w >= min_len:
            y_positions.append(y + h // 2)

    contours, _ = cv2.findContours(
        vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if h >= min_len:
            x_positions.append(x + w // 2)

    x_positions = _cluster_positions(x_positions, tol=4)
    y_positions = _cluster_positions(y_positions, tol=4)

    return x_positions, y_positions


def get_table_config() -> dict:
    def read_int(name: str, default: int) -> int:
        try:
            return int(os.getenv(name, str(default)))
        except ValueError:
            return default

    return {
        "vertical_strategy": os.getenv("PDF_TABLE_VERTICAL_STRATEGY", "lines"),
        "horizontal_strategy": os.getenv(
            "PDF_TABLE_HORIZONTAL_STRATEGY",
            "lines",
        ),
        "snap_tolerance": read_int("PDF_TABLE_SNAP_TOL", 3),
        "join_tolerance": read_int("PDF_TABLE_JOIN_TOL", 3),
        "edge_min_length": read_int("PDF_TABLE_EDGE_MIN_LEN", 3),
        "intersection_tolerance": read_int("PDF_TABLE_INTERSECTION_TOL", 3),
    }


def get_table_line_config() -> dict:
    def read_int(name: str, default: int) -> int:
        try:
            return int(os.getenv(name, str(default)))
        except ValueError:
            return default

    return {
        "line_detect": os.getenv("PDF_TABLE_LINE_DETECT", "1").strip() == "1",
        "line_min_len": read_int("PDF_TABLE_LINE_MIN_LEN", 40),
        "max_cells": read_int("PDF_TABLE_MAX_CELLS", 400),
    }


def extract_table_blocks(  # noqa: C901
    plumber_page,
    page_index: int,
    page_image,
    cfg: dict,
    force_cell_ocr: bool,
) -> list[dict]:
    """Robust table cell extraction with selectable-text and OCR fallbacks."""
    blocks: list[dict] = []
    if not plumber_page:
        return blocks

    try:
        tables = plumber_page.find_tables(table_settings=get_table_config())
    except Exception as e:
        LOGGER.warning("Table detection error page %s: %s", page_index + 1, e)
        return blocks

    if not tables:
        return blocks

    scale = float(cfg.get("dpi", 200)) / 72.0

    for table_idx, table in enumerate(tables, start=1):
        t_bbox = getattr(table, "bbox", None)
        if not t_bbox:
            continue
        
        # In pdfplumber 0.11.x, table.rows is a list of lists of Cell objects
        # table.extract() gives us the text strings
        rows_cells = getattr(table, "rows", [])
        rows_text = table.extract() or []
        
        if not rows_cells and not rows_text:
            continue
            
        LOGGER.info("Page %s: Processing table %s (%s rows)", 
                    page_index + 1, table_idx, len(rows_text))

        for r_idx, row in enumerate(rows_text):
            # Get the corresponding cells for this row if available
            current_row_cells = rows_cells[r_idx] if r_idx < len(rows_cells) else []
            
            for c_idx, text_item in enumerate(row):
                text = (text_item or "").strip()
                
                # 1. Get Coordinates
                cx0, ctop, cx1, cbottom = None, None, None, None
                if c_idx < len(current_row_cells):
                    cell_obj = current_row_cells[c_idx]
                    if hasattr(cell_obj, "bbox"):
                        cx0, ctop, cx1, cbottom = cell_obj.bbox
                    elif isinstance(cell_obj, (list, tuple)) and len(cell_obj) >= 4:
                        cx0, ctop, cx1, cbottom = cell_obj[:4]
                
                # Fallback coordinates if cell_obj missing
                if None in (cx0, ctop, cx1, cbottom):
                    # Estimate based on table bbox and grid
                    col_count = max(len(r) for r in rows_text) or 1
                    row_count = len(rows_text) or 1
                    cw, ch = (t_bbox[2] - t_bbox[0]) / col_count, (t_bbox[3] - t_bbox[1]) / row_count
                    cx0 = t_bbox[0] + c_idx * cw
                    ctop = t_bbox[1] + r_idx * ch
                    cx1 = cx0 + cw
                    cbottom = ctop + ch

                # 2. OCR Fallback for empty text layer
                if (not text or force_cell_ocr) and page_image:
                    try:
                        x0_px, y0_px = int(cx0 * scale), int(ctop * scale)
                        x1_px, y1_px = int(cx1 * scale), int(cbottom * scale)
                        if x1_px > x0_px and y1_px > y0_px:
                            cropped = enhance_image_for_ocr(page_image.crop((x0_px, y0_px, x1_px, y1_px)))
                            if cfg.get("engine") == "paddle":
                                ocr_res = paddle_ocr_image(cropped, cfg.get("lang", "eng"))
                                text = " ".join(l.get("text", "") for l in ocr_res).strip()
                            else:
                                text = pytesseract.image_to_string(
                                    cropped, 
                                    lang=cfg.get("lang", "eng"),
                                    config=f"--psm {cfg.get('psm', 6)} --oem 3"
                                ).strip()
                    except Exception as e:
                        LOGGER.debug("Cell OCR failed: %s", e)

                if not text or is_garbage_text(text):
                    continue

                # 3. Create block
                block = make_block(
                    slide_index=page_index,
                    shape_id=900000 + page_index * 10000 + table_idx * 1000 + r_idx * 50 + c_idx,
                    block_type="pdf_text_block",
                    source_text=text,
                    x=cx0,
                    y=ctop,
                    width=cx1 - cx0,
                    height=cbottom - ctop,
                )
                block.update({
                    "is_table": True,
                    "page_no": page_index + 1,
                    "table_no": table_idx,
                    "row_no": r_idx + 1,
                    "col_no": c_idx + 1,
                })
                blocks.append(block)
                
    return blocks
