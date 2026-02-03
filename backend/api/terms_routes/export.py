from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Response

from backend.services.term_repository import list_terms

router = APIRouter()


@router.get("/export")
async def term_export() -> Response:
    items = list_terms({})
    output = io.StringIO()
    fieldnames = [
        "term",
        "category",
        "status",
        "case_rule",
        "note",
        "source",
        "filename",
        "aliases",
        "created_by",
        "created_at",
        "updated_at",
    ]
    language_codes: set[str] = set()
    for item in items:
        for lang in item.get("languages", []):
            if lang.get("lang_code"):
                language_codes.add(lang["lang_code"])
    for code in sorted(language_codes):
        fieldnames.append(f"lang_{code}")

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for item in items:
        row = {
            "term": item.get("term", ""),
            "category": item.get("category_name") or "",
            "status": item.get("status") or "",
            "case_rule": item.get("case_rule") or "",
            "note": item.get("note") or "",
            "source": item.get("source") or "",
            "filename": item.get("filename") or "",
            "aliases": "|".join(item.get("aliases") or []),
            "created_by": item.get("created_by") or "",
            "created_at": item.get("created_at") or "",
            "updated_at": item.get("updated_at") or "",
        }
        for lang in item.get("languages", []):
            code = lang.get("lang_code")
            if not code:
                continue
            row[f"lang_{code}"] = lang.get("value") or ""
        writer.writerow(row)

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=terms_export.csv"},
    )
