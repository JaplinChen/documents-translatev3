from backend.api.docx import router as docx_router
from backend.api.export import router as export_router
from backend.api.llm import router as llm_router
from backend.api.pptx import router as pptx_router
from backend.api.pptx_translate import router as pptx_translate_router
from backend.api.preserve_terms import router as preserve_terms_router
from backend.api.prompts import router as prompt_router
from backend.api.tm import router as tm_router
from backend.api.token_stats import router as token_stats_router
from backend.api.xlsx import router as xlsx_router
from backend.api.pdf import router as pdf_router

__all__ = [
    "docx_router",
    "llm_router",
    "pptx_router",
    "pptx_translate_router",
    "tm_router",
    "prompt_router",
    "preserve_terms_router",
    "token_stats_router",
    "export_router",
    "xlsx_router",
    "pdf_router",
]
