from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.pdf.extract import get_ocr_config, get_poppler_path

router = APIRouter(prefix="/api/ocr")


class OcrSettings(BaseModel):
    dpi: int | None = None
    lang: str | None = None
    conf_min: int | None = None
    psm: int | None = None
    engine: str | None = None
    poppler_path: str | None = None


def _validate_range(
    name: str,
    value: int | None,
    min_val: int,
    max_val: int,
) -> None:
    if value is None:
        return
    if value < min_val or value > max_val:
        raise HTTPException(
            status_code=400,
            detail=f"{name} 必須介於 {min_val} 與 {max_val} 之間",
        )


@router.get("/settings")
async def get_settings() -> dict:
    cfg = get_ocr_config()
    return {
        "dpi": cfg["dpi"],
        "lang": cfg["lang"],
        "conf_min": cfg["conf_min"],
        "psm": cfg.get("psm", 6),
        "engine": cfg.get("engine", "tesseract"),
        "poppler_path": (
            os.getenv("PDF_POPPLER_PATH", "") or get_poppler_path() or ""
        ),
    }


@router.post("/settings")
async def update_settings(payload: OcrSettings) -> dict:
    _validate_range("dpi", payload.dpi, 50, 600)
    _validate_range("conf_min", payload.conf_min, 0, 100)
    _validate_range("psm", payload.psm, 3, 13)
    if (
        payload.engine is not None
        and payload.engine not in {"tesseract", "paddle"}
    ):
        raise HTTPException(
            status_code=400,
            detail="engine 只支援 tesseract 或 paddle",
        )

    if payload.dpi is not None:
        os.environ["PDF_OCR_DPI"] = str(payload.dpi)
    if payload.lang is not None:
        os.environ["PDF_OCR_LANG"] = payload.lang
    if payload.conf_min is not None:
        os.environ["PDF_OCR_CONF_MIN"] = str(payload.conf_min)
    if payload.psm is not None:
        os.environ["PDF_OCR_PSM"] = str(payload.psm)
    if payload.engine is not None:
        os.environ["PDF_OCR_ENGINE"] = payload.engine
    if payload.poppler_path is not None:
        os.environ["PDF_POPPLER_PATH"] = payload.poppler_path

    return await get_settings()
