"""DOCX API endpoints."""

from fastapi import APIRouter

from backend.api.docx_routes import apply, download, extract, history, translate

router = APIRouter(prefix="/api/docx")

router.include_router(extract.router)
router.include_router(apply.router)
router.include_router(download.router)
router.include_router(history.router)
router.include_router(translate.router)
