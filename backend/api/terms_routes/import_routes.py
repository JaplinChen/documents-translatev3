from __future__ import annotations

import csv
import io
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Response, UploadFile

from backend.api.terms_routes.import_utils import (
    _apply_mapping,
    _collect_language_fields,
    _normalize_text,
    _parse_aliases,
    _validate_row,
    _write_error_report,
)
from backend.api.terms_routes.models import ImportMappingPayload
from backend.services.term_repository import get_category_id_by_name, upsert_term_by_norm

router = APIRouter()
ERROR_REPORT_PATH = Path("data/terms_import_errors.csv")


@router.post("/import/preview")
async def term_import_preview(
    file: UploadFile = File(...),
    mapping: str | None = None,
) -> dict:
    content = (await file.read()).decode("utf-8")
    mapping_payload = (
        ImportMappingPayload.model_validate_json(mapping)
        if mapping
        else ImportMappingPayload(mapping={})
    )
    reader = csv.DictReader(io.StringIO(content))
    rows = []
    errors = []
    total = 0
    for idx, row in enumerate(reader, start=2):
        total += 1
        mapped_row = _apply_mapping(
            {k: (v or "").strip() for k, v in row.items()},
            mapping_payload.mapping,
        )
        normalized = {k: (v or "").strip() for k, v in mapped_row.items()}
        row_errors = _validate_row(normalized)
        if not mapping_payload.create_missing_category and _normalize_text(
            normalized.get("category")
        ):
            if get_category_id_by_name(normalized.get("category")) is None:
                row_errors.append("分類不存在")
        rows.append({"row": idx, "data": normalized, "errors": row_errors})
        if row_errors:
            errors.append({"row": idx, "errors": row_errors})
    return {
        "rows": rows,
        "errors": errors,
        "summary": {
            "total": total,
            "valid": total - len(errors),
            "invalid": len(errors),
        },
    }


@router.post("/import")
async def term_import(
    file: UploadFile = File(...),
    mapping: str | None = None,
) -> dict:
    content = (await file.read()).decode("utf-8")
    mapping_payload = (
        ImportMappingPayload.model_validate_json(mapping)
        if mapping
        else ImportMappingPayload(mapping={})
    )
    reader = csv.DictReader(io.StringIO(content))
    imported = 0
    failed = []
    for idx, row in enumerate(reader, start=2):
        mapped_row = _apply_mapping(
            {k: (v or "").strip() for k, v in row.items()},
            mapping_payload.mapping,
        )
        normalized = {k: (v or "").strip() for k, v in mapped_row.items()}
        row_errors = _validate_row(normalized)
        if row_errors:
            failed.append({"row": idx, "errors": row_errors})
            continue
        languages = _collect_language_fields(normalized)
        payload = {
            "term": normalized.get("term"),
            "category_name": normalized.get("category"),
            "status": normalized.get("status") or "active",
            "case_rule": normalized.get("case_rule") or None,
            "note": normalized.get("note") or None,
            "aliases": _parse_aliases(normalized.get("aliases", "")),
            "languages": languages,
            "created_by": normalized.get("created_by") or None,
            "allow_create_category": mapping_payload.create_missing_category,
        }
        try:
            upsert_term_by_norm(payload)
            imported += 1
        except ValueError as exc:
            failed.append({"row": idx, "errors": [str(exc)]})
    _write_error_report(ERROR_REPORT_PATH, failed)
    return {
        "imported": imported,
        "failed": failed,
        "error_report_url": "/api/terms/import/errors" if failed else None,
    }


@router.get("/import/errors")
async def term_import_errors() -> Response:
    if not ERROR_REPORT_PATH.exists():
        raise HTTPException(status_code=404, detail="尚無錯誤報表")
    content = ERROR_REPORT_PATH.read_text(encoding="utf-8")
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=terms_import_errors.csv"},
    )
