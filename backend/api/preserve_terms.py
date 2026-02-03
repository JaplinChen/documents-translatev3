from __future__ import annotations

import csv
import io
from fastapi import APIRouter, Body, HTTPException, Response
from pydantic import BaseModel

from backend.services.language_detect import detect_language
from backend.services.preserve_terms_repository import (
    create_preserve_term as repo_create_preserve_term,
    create_preserve_terms_batch as repo_create_preserve_terms_batch,
    delete_all_preserve_terms as repo_delete_all_preserve_terms,
    delete_preserve_term as repo_delete_preserve_term,
    get_preserve_term_by_id as repo_get_preserve_term_by_id,
    list_preserve_terms as repo_list_preserve_terms,
    update_preserve_term as repo_update_preserve_term,
)
from backend.services.translation_memory_adapter import upsert_glossary

router = APIRouter(prefix="/api/preserve-terms")


class PreserveTerm(BaseModel):
    id: str | None = None
    term: str
    category: str = "未分類"
    case_sensitive: bool = True
    created_at: str | None = None


class ConvertToGlossaryRequest(BaseModel):
    id: str
    target_lang: str = "zh-TW"
    priority: int = 10


class PreserveTermBatch(BaseModel):
    terms: list[PreserveTerm]


@router.get("")
async def get_preserve_terms() -> dict:
    """Get all preserve terms."""
    return {"terms": repo_list_preserve_terms()}


@router.post("")
async def create_preserve_term(term: PreserveTerm) -> dict:
    """Create a new preserve term."""
    try:
        new_term = repo_create_preserve_term(
            term=term.term,
            category=term.category,
            case_sensitive=term.case_sensitive,
        )
        return {"term": new_term}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/batch")
async def create_preserve_terms_batch(payload: PreserveTermBatch) -> dict:
    """Create preserve terms in batch, skipping duplicates."""
    entries = [
        {
            "term": entry.term,
            "category": entry.category,
            "case_sensitive": entry.case_sensitive,
        }
        for entry in payload.terms
    ]
    return repo_create_preserve_terms_batch(entries)


@router.put("/{term_id}")
async def update_preserve_term(term_id: str, term: PreserveTerm) -> dict:
    """Update an existing preserve term."""
    try:
        updated = repo_update_preserve_term(
            term_id=term_id,
            term=term.term,
            category=term.category,
            case_sensitive=term.case_sensitive,
        )
        return {"term": updated}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{term_id}")
async def delete_preserve_term(term_id: str) -> dict:
    """Delete a preserve term."""
    try:
        deleted = repo_delete_preserve_term(term_id)
        return {"deleted": deleted}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/export")
async def export_preserve_terms() -> Response:
    """Export preserve terms as CSV."""
    terms = repo_list_preserve_terms()

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["term", "category", "case_sensitive"],
    )
    writer.writeheader()

    for term in terms:
        writer.writerow(
            {
                "term": term["term"],
                "category": term.get("category", "未分類"),
                "case_sensitive": term.get("case_sensitive", True),
            }
        )

    csv_content = output.getvalue()

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=preserve_terms.csv"
        },
    )


@router.post("/import")
async def import_preserve_terms(
    csv_data: str = Body(..., media_type="text/plain"),
) -> dict:
    """Import preserve terms from CSV data."""
    try:
        text = csv_data.lstrip("\ufeff")
        if not text.strip():
            total = len(repo_list_preserve_terms())
            return {"imported": 0, "skipped": 0, "total": total}
        reader = csv.DictReader(io.StringIO(text))

        imported = 0
        skipped = 0
        payload_terms = []

        for row in reader:
            term_text = row.get("term", "").strip()
            if not term_text:
                continue
            payload_terms.append(
                {
                    "term": term_text,
                    "category": row.get("category", "未分類").strip(),
                    "case_sensitive": row.get("case_sensitive", "true").lower() == "true",
                }
            )
        result = repo_create_preserve_terms_batch(payload_terms)
        imported = result.get("created", 0)
        skipped = result.get("skipped", 0)
        total = len(repo_list_preserve_terms())
        return {"imported": imported, "skipped": skipped, "total": total}

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"CSV 匯入失敗: {str(exc)}",
        ) from exc


@router.delete("")
async def delete_all_preserve_terms() -> dict:
    """Delete all preserve terms."""
    repo_delete_all_preserve_terms()
    return {"message": "已清除所有保留術語"}


@router.post("/convert-from-glossary")
async def convert_glossary_to_preserve_term(
    source_text: str,
    category: str = "未分類",
    case_sensitive: bool = True,
) -> dict:
    """Convert a glossary entry's source_text to a preserve term.

    This allows users to mark a term from the translation glossary
    as a technical term that should not be translated.
    """
    if not source_text or not source_text.strip():
        raise HTTPException(status_code=400, detail="術語不可為空")

    term_text = source_text.strip()
    try:
        new_term = repo_create_preserve_term(
            term=term_text,
            category=category,
            case_sensitive=case_sensitive,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"term": new_term, "message": f"已將 '{term_text}' 添加到保留術語"}


@router.post("/convert-to-glossary")
async def convert_preserve_term_to_glossary(
    payload: ConvertToGlossaryRequest,
) -> dict:
    """Convert a preserve term to glossary entry with auto-detected source lang."""
    term_entry = repo_get_preserve_term_by_id(payload.id)
    if term_entry is None:
        raise HTTPException(status_code=404, detail="術語不存在")

    term_text = term_entry.get("term", "").strip()
    if not term_text:
        raise HTTPException(status_code=400, detail="術語不可為空")

    detected_lang = detect_language(term_text) or "auto"
    upsert_glossary(
        {
            "source_lang": detected_lang,
            "target_lang": payload.target_lang,
            "source_text": term_text,
            "target_text": term_text,
            "priority": payload.priority,
        }
    )

    repo_delete_preserve_term(payload.id)

    return {
        "status": "ok",
        "source_lang": detected_lang,
        "target_lang": payload.target_lang,
    }
