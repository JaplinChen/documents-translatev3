from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

router = APIRouter(prefix="/api/preserve-terms")

PRESERVE_TERMS_FILE = (
    Path(__file__).parent.parent / "data" / "preserve_terms.json"
)


class PreserveTerm(BaseModel):
    id: str | None = None
    term: str
    category: str = "未分類"
    case_sensitive: bool = True
    created_at: str | None = None


def _load_preserve_terms() -> list[dict]:
    """Load preserve terms from JSON file."""
    if not PRESERVE_TERMS_FILE.exists():
        return []
    try:
        with open(PRESERVE_TERMS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_preserve_terms(terms: list[dict]) -> None:
    """Save preserve terms to JSON file."""
    PRESERVE_TERMS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PRESERVE_TERMS_FILE, "w", encoding="utf-8") as f:
        json.dump(terms, f, ensure_ascii=False, indent=2)


@router.get("")
async def get_preserve_terms() -> dict:
    """Get all preserve terms."""
    terms = _load_preserve_terms()
    return {"terms": terms}


@router.post("")
async def create_preserve_term(term: PreserveTerm) -> dict:
    """Create a new preserve term."""
    terms = _load_preserve_terms()

    # Check for duplicates
    for existing in terms:
        if existing["term"].lower() == term.term.lower():
            raise HTTPException(
                status_code=400,
                detail=f"術語 '{term.term}' 已存在",
            )

    new_term = {
        "id": str(uuid4()),
        "term": term.term,
        "category": term.category,
        "case_sensitive": term.case_sensitive,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }

    terms.append(new_term)
    _save_preserve_terms(terms)

    return {"term": new_term}


@router.put("/{term_id}")
async def update_preserve_term(term_id: str, term: PreserveTerm) -> dict:
    """Update an existing preserve term."""
    terms = _load_preserve_terms()

    for i, existing in enumerate(terms):
        if existing["id"] == term_id:
            terms[i]["term"] = term.term
            terms[i]["category"] = term.category
            terms[i]["case_sensitive"] = term.case_sensitive
            _save_preserve_terms(terms)
            return {"term": terms[i]}

    raise HTTPException(status_code=404, detail="術語不存在")


@router.delete("/{term_id}")
async def delete_preserve_term(term_id: str) -> dict:
    """Delete a preserve term."""
    terms = _load_preserve_terms()

    for i, existing in enumerate(terms):
        if existing["id"] == term_id:
            deleted = terms.pop(i)
            _save_preserve_terms(terms)
            return {"deleted": deleted}

    raise HTTPException(status_code=404, detail="術語不存在")


@router.get("/export")
async def export_preserve_terms() -> Response:
    """Export preserve terms as CSV."""
    terms = _load_preserve_terms()

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
async def import_preserve_terms(csv_data: str) -> dict:
    """Import preserve terms from CSV data."""
    try:
        terms = _load_preserve_terms()
        reader = csv.DictReader(io.StringIO(csv_data))

        imported = 0
        skipped = 0

        for row in reader:
            term_text = row.get("term", "").strip()
            if not term_text:
                continue

            # Check for duplicates
            exists = any(
                existing["term"].lower() == term_text.lower()
                for existing in terms
            )

            if exists:
                skipped += 1
                continue

            new_term = {
                "id": str(uuid4()),
                "term": term_text,
                "category": row.get("category", "未分類").strip(),
                "case_sensitive": (
                    row.get("case_sensitive", "true").lower() == "true"
                ),
                "created_at": datetime.utcnow().isoformat() + "Z",
            }

            terms.append(new_term)
            imported += 1

        _save_preserve_terms(terms)

        return {"imported": imported, "skipped": skipped, "total": len(terms)}

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"CSV 匯入失敗: {str(exc)}",
        ) from exc


@router.delete("")
async def delete_all_preserve_terms() -> dict:
    """Delete all preserve terms."""
    _save_preserve_terms([])
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
    terms = _load_preserve_terms()

    # Check for duplicates
    for existing in terms:
        if existing["term"].lower() == term_text.lower():
            raise HTTPException(
                status_code=400,
                detail=f"術語 '{term_text}' 已存在於保留術語中",
            )

    new_term = {
        "id": str(uuid4()),
        "term": term_text,
        "category": category,
        "case_sensitive": case_sensitive,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }

    terms.append(new_term)
    _save_preserve_terms(terms)

    return {"term": new_term, "message": f"已將 '{term_text}' 添加到保留術語"}
