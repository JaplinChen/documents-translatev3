from backend.api.docx import router as docx_router
from backend.api.llm import router as llm_router
from backend.api.pptx import router as pptx_router
from backend.api.prompts import router as prompt_router
from backend.api.tm import router as tm_router

__all__ = ["docx_router", "llm_router", "pptx_router", "tm_router", "prompt_router"]
