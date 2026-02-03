from __future__ import annotations

from fastapi import APIRouter

from backend.api.terms_routes.batch import router as batch_router
from backend.api.terms_routes.categories import router as categories_router
from backend.api.terms_routes.core import router as core_router
from backend.api.terms_routes.export import router as export_router
from backend.api.terms_routes.import_routes import router as import_router
from backend.api.terms_routes.sync import router as sync_router

router = APIRouter(prefix="/api/terms")
router.include_router(core_router)
router.include_router(batch_router)
router.include_router(sync_router)
router.include_router(categories_router)
router.include_router(import_router)
router.include_router(export_router)
