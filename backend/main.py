from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import docx_router, llm_router, pptx_router, prompt_router, tm_router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5193", "http://127.0.0.1:5193"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(docx_router)
app.include_router(pptx_router)
app.include_router(tm_router)
app.include_router(llm_router)
app.include_router(prompt_router)
