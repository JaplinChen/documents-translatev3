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
            table_cfg = get_table_line_config()
            rows = table.extract() or []
            table_bbox = getattr(table, "bbox", None)
            if not table_bbox:
                continue
            table_x0, table_top, table_x1, table_bottom = table_bbox
            # 優先使用線條偵測切格
            if table_cfg["line_detect"] and page_image is not None:
                scale = float(cfg.get("dpi", 200)) / 72.0
                img = np.array(page_image)
                x0_px = max(0, int(table_x0 * scale))
                y0_px = max(0, int(table_top * scale))
                x1_px = min(img.shape[1], int(table_x1 * scale))
                y1_px = min(img.shape[0], int(table_bottom * scale))
                if x1_px > x0_px and y1_px > y0_px:
                    crop = img[y0_px:y1_px, x0_px:x1_px]
                    xs, ys = _detect_table_grid_lines(
                        crop, table_cfg["line_min_len"]
                    )
                    xs = [0] + [x for x in xs if 0 < x < crop.shape[1]] + [crop.shape[1]]
                    ys = [0] + [y for y in ys if 0 < y < crop.shape[0]] + [crop.shape[0]]
                    xs = sorted(set(xs))
                    ys = sorted(set(ys))
                    cell_count = (len(xs) - 1) * (len(ys) - 1)
                    if len(xs) >= 2 and len(ys) >= 2 and cell_count <= table_cfg["max_cells"]:
                        cell_index = 0
                        for r_idx in range(len(ys) - 1):
                            for c_idx in range(len(xs) - 1):
                                cell_index += 1
                                cx0 = x0_px + xs[c_idx]
                                cx1 = x0_px + xs[c_idx + 1]
                                cy0 = y0_px + ys[r_idx]
                                cy1 = y0_px + ys[r_idx + 1]
                                if cx1 <= cx0 or cy1 <= cy0:
                                    continue
                                cropped = enhance_image_for_ocr(
                                    page_image.crop((cx0, cy0, cx1, cy1))
                                )
                                if cfg.get("engine") == "paddle":
                                    ocr_lines = paddle_ocr_image(
                                        cropped, cfg.get("lang", "eng")
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
                                x0 = cx0 / scale
                                x1 = cx1 / scale
                                top = cy0 / scale
                                bottom = cy1 / scale
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
                                        "row_no": r_idx + 1,
                                        "col_no": c_idx + 1,
                                    }
                                )
                                blocks.append(block)
                        continue

            # 線條偵測失敗就回退平均切格
            if not rows:
                continue
            row_count = len(rows)
            col_count = max((len(r) for r in rows), default=0)
            if row_count <= 0 or col_count <= 0:
                continue
            row_h = (table_bottom - table_top) / row_count
            col_w = (table_x1 - table_x0) / col_count
            for r_idx, row in enumerate(rows, start=1):
                for c_idx, cell_text in enumerate(row, start=1):
                    text = (cell_text or "").strip()
                    if (
                        not text
                        or is_noisy_text(text)
                        or is_numeric_only(text)
                        or is_technical_terms_only(text)
                        or is_garbage_text(text)
                    ):
                        continue
                    x0 = table_x0 + (c_idx - 1) * col_w
                    x1 = table_x0 + c_idx * col_w
                    top = table_top + (r_idx - 1) * row_h
                    bottom = table_top + r_idx * row_h
                    block = make_block(
                        page_index,
                        900000
                        + page_index * 100000
                        + table_index * 1000
                        + r_idx * 50
                        + c_idx,
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
                            "row_no": r_idx,
                            "col_no": c_idx,
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
