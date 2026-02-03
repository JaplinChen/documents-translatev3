"""PPTX translation API endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from backend.api.pptx_routes.models import TranslateRequest
from backend.api.pptx_routes.stream import pptx_translate_stream
from backend.api.pptx_routes.translate import pptx_translate

from backend.api.pptx_routes.stream import router as stream_router
from backend.api.pptx_routes.translate import router as translate_router

router = APIRouter(prefix="/api/pptx")
router.include_router(translate_router)
router.include_router(stream_router)

__all__ = [
    "TranslateRequest",
    "pptx_translate",
    "pptx_translate_stream",
    "router",
]
