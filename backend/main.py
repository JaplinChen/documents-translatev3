import asyncio
import time
import shutil
import os
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from backend.api import (
    docx_router,
    export_router,
    llm_router,
    pptx_router,
    pptx_translate_router,
    preserve_terms_router,
    prompt_router,
    tm_router,
    token_stats_router,
    xlsx_router,
    pdf_router,
    ocr_settings_router,
    style_router,
)

from backend.tools.logging_middleware import StructuredLoggingMiddleware

app = FastAPI()
app.add_middleware(StructuredLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "X-Request-ID"],
)

app.include_router(docx_router)
app.include_router(pptx_router)
app.include_router(pptx_translate_router)
app.include_router(tm_router)
app.include_router(llm_router)
app.include_router(prompt_router)
app.include_router(preserve_terms_router)
app.include_router(token_stats_router)
app.include_router(xlsx_router)
app.include_router(pdf_router)
app.include_router(ocr_settings_router)
app.include_router(style_router)
app.include_router(export_router)


@app.post("/api/admin/reset-cache")
async def reset_cache():
    """Nuclear reset: Delete all databases and exports."""
    data_dir = Path("data")
    count = 0
    if data_dir.exists():
        for item in data_dir.glob("**/*"):
            if item.is_file() and (item.suffix in (".db", ".json", ".pptx", ".docx") or "cache" in item.name):
                try:
                    os.remove(item)
                    count += 1
                except Exception:
                    pass
    return {"status": "success", "deleted_files": count}


async def cleanup_exports_task():
    """Background task to remove old export files (older than 1 hour)."""
    export_dir = Path("data/exports")
    while True:
        try:
            if export_dir.exists():
                now = time.time()
                for item in export_dir.iterdir():
                    if item.is_file() and now - item.stat().st_mtime > 1800:
                        item.unlink()
        except Exception as e:
            print(f"Cleanup error: {e}")
        await asyncio.sleep(1800)  # Run every 30 mins


@app.on_event("startup")
async def startup_event():
    # Ensure exports directory exists
    Path("data/exports").mkdir(parents=True, exist_ok=True)
    # Start cleanup task
    asyncio.create_task(cleanup_exports_task())


@app.get("/health")
def health_check():
    """Health check endpoint for Docker/Kubernetes."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=5002, reload=True)
