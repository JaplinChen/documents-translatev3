import starlette.formparsers

# Increase the maximum size for a single part in a multipart form request.
# The default is 1,048,576 bytes (1MB). We increase it to 50MB to handle large block lists.
# This must happen as early as possible.
starlette.formparsers.MultiPartParser.max_part_size = 50 * 1024 * 1024

import asyncio
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api import (
    docx_router,
    export_router,
    layouts_router,
    llm_router,
    ocr_settings_router,
    pdf_router,
    pptx_router,
    pptx_translate_router,
    preserve_terms_router,
    prompt_router,
    style_router,
    terms_router,
    tm_router,
    token_stats_router,
    xlsx_router,
)
from backend.tools.logging_middleware import StructuredLoggingMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure exports directory exists
    Path("data/exports").mkdir(parents=True, exist_ok=True)
    Path("data/thumbnails").mkdir(parents=True, exist_ok=True)

    cleanup_task = asyncio.create_task(cleanup_exports_task())
    stats_task = asyncio.create_task(learning_stats_task())
    tasks = [cleanup_task, stats_task]

    try:
        yield
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


app = FastAPI(lifespan=lifespan)
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
app.include_router(layouts_router)
app.include_router(prompt_router)
app.include_router(preserve_terms_router)
app.include_router(terms_router)
app.include_router(token_stats_router)
app.include_router(xlsx_router)
app.include_router(pdf_router)
app.include_router(ocr_settings_router)
app.include_router(style_router)
app.include_router(export_router)

# Mount thumbnails as static files
app.mount("/thumbnails", StaticFiles(directory="data/thumbnails"), name="thumbnails")


@app.post("/api/admin/reset-cache")
async def reset_cache():
    """Safe reset: Delete exports and temporary document files, preserving core databases."""
    data_dir = Path("data")
    export_dir = data_dir / "exports"
    count = 0

    # 1. Clean exports directory
    if export_dir.exists():
        for item in export_dir.glob("*"):
            if item.is_file():
                try:
                    os.remove(item)
                    count += 1
                except Exception:
                    pass

    # 3. Clean thumbnails
    thumb_dir = data_dir / "thumbnails"
    if thumb_dir.exists():
        for item in thumb_dir.glob("*"):
            if item.is_file():
                try:
                    os.remove(item)
                    count += 1
                except Exception:
                    pass

    # 4. Clean SQLite document cache
    try:
        import sqlite3
        cache_db = data_dir / "cache.db"
        if cache_db.exists():
            with sqlite3.connect(cache_db) as conn:
                conn.execute("DELETE FROM document_cache")
                count += 1
    except Exception:
        pass

    return {"status": "success", "deleted_files": count}


async def cleanup_exports_task():
    """Background task to remove old export files (older than 1 hour)."""
    export_dir = Path("data/exports")
    thumb_dir = Path("data/thumbnails")
    while True:
        try:
            now = time.time()
            # Clean exports
            if export_dir.exists():
                for item in export_dir.iterdir():
                    if item.is_file() and now - item.stat().st_mtime > 1800:
                        item.unlink()
            # Clean thumbnails
            if thumb_dir.exists():
                for item in thumb_dir.iterdir():
                    if item.is_file() and now - item.stat().st_mtime > 3600:
                        item.unlink()
        except Exception as e:
            print(f"Cleanup error: {e}")
        await asyncio.sleep(1800)  # Run every 30 mins


async def learning_stats_task():
    """Background task to compute daily learning stats."""
    from backend.workers.learning_stats import run_daily_stats

    while True:
        try:
            run_daily_stats(scope_type="project", scope_id="default", days_back=1)
        except Exception as e:
            print(f"Learning stats error: {e}")
        await asyncio.sleep(24 * 60 * 60)


@app.get("/health")
def health_check():
    """Health check endpoint for Docker/Kubernetes."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=5005, reload=True, proxy_headers=True, forwarded_allow_ips='*')

