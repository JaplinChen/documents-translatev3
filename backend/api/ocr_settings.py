from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.pdf.extract import get_ocr_config, get_poppler_path
from backend.services.pdf.ocr_paddle import is_paddle_gpu_available

router = APIRouter(prefix="/api/ocr")


class OcrSettings(BaseModel):
    dpi: int | None = None
    lang: str | None = None
    conf_min: int | None = None
    psm: int | None = None
    engine: str | None = None
    allow_paddle: bool | None = None
    paddle_fallback: bool | None = None
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
    try:
        cfg = get_ocr_config()
        return {
            "dpi": cfg["dpi"],
            "lang": cfg["lang"],
            "conf_min": cfg["conf_min"],
            "psm": cfg.get("psm", 6),
            "engine": cfg.get("engine", "tesseract"),
            "allow_paddle": cfg.get("allow_paddle", False),
            "paddle_fallback": cfg.get("paddle_fallback", False),
            "poppler_path": (
                os.getenv("PDF_POPPLER_PATH", "") or get_poppler_path() or ""
            ),
        }
    except Exception as e:
        # Fallback to defaults to prevent API crash (400/500)
        return {
            "dpi": 300,
            "lang": "chi_tra+vie+eng",
            "conf_min": 10,
            "psm": 6,
            "engine": "tesseract",
            "allow_paddle": False,
            "paddle_fallback": False,
            "poppler_path": "",
            "error_hint": str(e)
        }


@router.post("/settings")
async def update_settings(payload: OcrSettings) -> dict:
    disable_paddle = os.getenv("PDF_OCR_DISABLE_PADDLE", "0").strip() == "1"
    paddle_gpu_available = is_paddle_gpu_available()
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
    if disable_paddle and payload.engine == "paddle":
        raise HTTPException(
            status_code=400,
            detail="此環境已停用 PaddleOCR",
        )

    if payload.engine == "paddle" and not paddle_gpu_available:
        raise HTTPException(
            status_code=400,
            detail="PaddleOCR 需要可用的 GPU",
        )

    if payload.allow_paddle is True and not paddle_gpu_available:
        raise HTTPException(
            status_code=400,
            detail="PaddleOCR 需要可用的 GPU",
        )

    if disable_paddle and payload.allow_paddle is True:
        raise HTTPException(
            status_code=400,
            detail="此環境已停用 PaddleOCR",
        )

    if payload.engine is not None:
        os.environ["PDF_OCR_ENGINE"] = payload.engine
    if payload.allow_paddle is not None:
        os.environ["PDF_OCR_ALLOW_PADDLE"] = "1" if payload.allow_paddle else "0"
    if payload.paddle_fallback is not None:
        os.environ["PDF_OCR_PADDLE_FALLBACK"] = "1" if payload.paddle_fallback else "0"
    if payload.poppler_path is not None:
        os.environ["PDF_POPPLER_PATH"] = payload.poppler_path

    return await get_settings()
