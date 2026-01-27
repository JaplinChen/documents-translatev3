import logging
import os

import pytesseract

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


def extract_table_blocks(  # noqa: C901
    plumber_page,
    page_index: int,
    page_image,
    cfg: dict,
    force_cell_ocr: bool,
) -> list[dict]:
    blocks = []
    if not plumber_page:
        return blocks
    try:
        tables = plumber_page.find_tables(table_settings=get_table_config())
    except Exception as e:
        LOGGER.warning(
            "pdf table detect failed page=%s: %s",
            page_index + 1,
            e,
        )
        return blocks

    for table_index, table in enumerate(tables, start=1):
        cells = getattr(table, "cells", [])

        if not cells:
            rows = table.extract() or []
            row_texts = [
                "\t".join(cell or "" for cell in row).strip()
                for row in rows
                if row
            ]
            full_text = "\n".join([r for r in row_texts if r]).strip()
            if (
                not full_text
                or is_noisy_text(full_text)
                or is_numeric_only(full_text)
                or is_technical_terms_only(full_text)
                or is_garbage_text(full_text)
            ):
                continue
            x0, top, x1, bottom = table.bbox
            block = make_block(
                page_index,
                900000 + page_index * 1000 + table_index,
                "pdf_text_block",
                full_text,
                x0,
                top,
                x1 - x0,
                bottom - top,
            )
            block.update(
                {
                    "is_table": True,
                    "page_no": page_index + 1,
                    "table_no": table_index,
                }
            )
            blocks.append(block)
            continue

        scale = float(cfg.get("dpi", 200)) / 72.0
        for cell_index, cell in enumerate(cells, start=1):
            x0 = cell.get("x0")
            top = cell.get("top")
            x1 = cell.get("x1")
            bottom = cell.get("bottom")
            if None in (x0, top, x1, bottom):
                continue
            text = (cell.get("text") or "").strip()

            if force_cell_ocr or not text:
                if page_image:
                    cropped = enhance_image_for_ocr(
                        page_image.crop(
                            (
                                int(x0 * scale),
                                int(top * scale),
                                int(x1 * scale),
                                int(bottom * scale),
                            )
                        )
                    )
                    if cfg.get("engine") == "paddle":
                        ocr_lines = paddle_ocr_image(
                            cropped,
                            cfg.get("lang", "eng"),
                        )
                        text = " ".join(
                            line.get("text", "") for line in ocr_lines
                        ).strip()
                    else:
                        text = (
                            pytesseract.image_to_string(
                                cropped,
                                lang=cfg.get("lang", "eng"),
                                config=f"--psm {cfg.get('psm', 6)}",
                            )
                            or ""
                        ).strip()

            if (
                not text
                or is_noisy_text(text)
                or is_numeric_only(text)
                or is_technical_terms_only(text)
                or is_garbage_text(text)
            ):
                continue
            block = make_block(
                page_index,
                900000
                + page_index * 100000
                + table_index * 1000
                + cell_index,
                "pdf_text_block",
                text,
                x0,
                top,
                x1 - x0,
                bottom - top,
            )
            block.update(
                {
                    "is_table": True,
                    "page_no": page_index + 1,
                    "table_no": table_index,
                    "cell_no": cell_index,
                }
            )
            blocks.append(block)
    return blocks
