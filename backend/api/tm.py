from __future__ import annotations

from fastapi import APIRouter

from backend.api.tm_routes.categories import router as categories_router
from backend.api.tm_routes.extract import router as extract_router
from backend.api.tm_routes.feedback import router as feedback_router
from backend.api.tm_routes.glossary import router as glossary_router
from backend.api.tm_routes.learning import router as learning_router
from backend.api.tm_routes.memory import router as memory_router
from backend.api.tm_routes.seed import router as seed_router

router = APIRouter(prefix="/api/tm")
router.include_router(seed_router)
router.include_router(glossary_router)
router.include_router(memory_router)
router.include_router(learning_router)
router.include_router(categories_router)
router.include_router(extract_router)
router.include_router(feedback_router)
