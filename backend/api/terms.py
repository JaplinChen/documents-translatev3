from __future__ import annotations

import csv
import io
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, Response, UploadFile
from pydantic import BaseModel
import socket

from backend.services.term_repository import (
    batch_delete_terms,
    batch_update_terms,
    create_category,
    create_term,
    delete_category,
    delete_term,
    get_category_id_by_name,
    list_categories,
    list_terms,
    list_versions,
    sync_from_external,
    update_category,
    update_term,
    upsert_term_by_norm,
)

router = APIRouter(prefix="/api/terms")
ERROR_REPORT_PATH = Path("data/terms_import_errors.csv")


class TermLanguageInput(BaseModel):
    lang_code: str
    value: str | None = None


class TermPayload(BaseModel):
    term: str
    category_id: int | None = None
    category_name: str | None = None
    status: str = "active"
    case_rule: str | None = None
    note: str | None = None
    source: str | None = None
    filename: str | None = None
    aliases: list[str] = []
    languages: list[TermLanguageInput] = []
    created_by: str | None = None
    source_lang: str | None = None
    target_lang: str | None = None
    priority: int | None = 0


class CategoryPayload(BaseModel):
    name: str
    sort_order: int | None = None


class BatchPayload(BaseModel):
    ids: list[int]
    category_id: int | None = None
    status: str | None = None
    case_rule: str | None = None
    source: str | None = None
    priority: int | None = None


class ImportMappingPayload(BaseModel):
    mapping: dict[str, str]
    create_missing_category: bool = True


@router.get("")
async def term_list(
    q: str | None = None,
    category_id: int | None = None,
    status: str | None = None,
    missing_lang: str | None = None,
    has_alias: bool | None = None,
    created_by: str | None = None,
    filename: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    items = list_terms(
        {
            "q": q,
            "category_id": category_id,
            "status": status,
            "missing_lang": missing_lang,
            "has_alias": has_alias,
            "created_by": created_by,
            "filename": filename,
            "date_from": date_from,
            "date_to": date_to,
        }
    )
    return {"items": items}


@router.post("")
async def term_create(payload: TermPayload, request: Request) -> dict:
    try:
        if not payload.created_by:
            client_host = request.client.host
            try:
                # Try to resolve hostname
                hostname, _, _ = socket.gethostbyaddr(client_host)
                payload.created_by = hostname
            except Exception:
                # Fallback to IP if resolution fails
                payload.created_by = client_host

        item = create_term(payload.model_dump())
        return {"item": item}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/upsert")
async def term_upsert(payload: TermPayload, request: Request) -> dict:
    try:
        if not payload.created_by:
            client_host = request.client.host
            try:
                hostname, _, _ = socket.gethostbyaddr(client_host)
                payload.created_by = hostname
            except Exception:
                payload.created_by = client_host

        # Use upsert_term_by_norm which handles existing terms
        item = upsert_term_by_norm(payload.model_dump())
        return {"item": item}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/{term_id}")
async def term_update(term_id: int, payload: TermPayload) -> dict:
    try:
        item = update_term(term_id, payload.model_dump())
        return {"item": item}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{term_id}")
async def term_delete(term_id: int) -> dict:
    try:
        delete_term(term_id)
        return {"status": "ok"}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{term_id}/versions")
async def term_versions(term_id: int) -> dict:
    items = list_versions(term_id)
    return {"items": items}


@router.post("/batch")
async def term_batch_update(payload: BatchPayload) -> dict:
    try:
        updated = batch_update_terms(
            payload.ids,
            category_id=payload.category_id,
            status=payload.status,
            case_rule=payload.case_rule,
            source=payload.source,
            priority=payload.priority,
        )
        return {"updated": updated}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/batch")
async def term_batch_delete(payload: BatchPayload) -> dict:
    deleted = batch_delete_terms(payload.ids)
    return {"deleted": deleted}


@router.post("/sync-all")
async def term_sync_all() -> dict:
    """Synchronize all existing data from preserve_terms and glossary to terms center."""
    from backend.services.preserve_terms_repository import list_preserve_terms
    from backend.services.translation_memory import get_glossary

    synced_count = 0
    # 1. Sync preserve terms (術語)
    p_terms = list_preserve_terms()
    for pt in p_terms:
        try:
            # Map boolean case_sensitive to enum case_rule
            case_rule = "uppercase" if pt.get("case_sensitive") else "preserve"
            sync_from_external(
                pt["term"],
                category_name=pt.get("category"),
                source="terminology",
                case_rule=case_rule,
            )
            synced_count += 1
        except Exception as e:
            print(f"Sync sync-all preserve failed for {pt['term']}: {e}")

    # 2. Sync glossary (對照表)
    g_terms = get_glossary(limit=5000)
    for gt in g_terms:
        try:
            lang_code = gt.get("target_lang", "zh-TW")
            sync_from_external(
                gt["source_text"],
                category_name=gt.get("category_name"),
                source="reference",
                source_lang=gt.get("source_lang"),
                target_lang=gt.get("target_lang"),
                priority=gt.get("priority", 0),
                languages=[{"lang_code": lang_code, "value": gt["target_text"]}],
            )
            synced_count += 1
        except Exception as e:
            print(f"Sync sync-all glossary failed for {gt['source_text']}: {e}")

    return {"status": "ok", "synced": synced_count}


@router.get("/categories")
async def category_list() -> dict:
    return {"items": list_categories()}


@router.post("/categories")
async def category_create(payload: CategoryPayload) -> dict:
    try:
        item = create_category(payload.name, payload.sort_order)
        return {"item": item}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/categories/{category_id}")
async def category_update(category_id: int, payload: CategoryPayload) -> dict:
    try:
        item = update_category(category_id, payload.name, payload.sort_order)
        return {"item": item}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/categories/{category_id}")
async def category_delete(category_id: int) -> dict:
    try:
        delete_category(category_id)
        return {"status": "ok"}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return " ".join(text.strip().split())


def _parse_aliases(raw: str) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split("|") if item.strip()]


def _validate_row(row: dict) -> list[str]:
    errors = []
    term = _normalize_text(row.get("term"))
    category = _normalize_text(row.get("category"))
    status = _normalize_text(row.get("status")) or "active"
    case_rule = _normalize_text(row.get("case_rule"))
    if not term:
        errors.append("term 必填")
    if not category:
        errors.append("category 必填")
    if status not in {"active", "inactive"}:
        errors.append("status 需為 active/inactive")
    if case_rule and case_rule not in {"preserve", "uppercase", "lowercase"}:
        errors.append("case_rule 需為 preserve/uppercase/lowercase")
    return errors


def _apply_mapping(row: dict, mapping: dict[str, str]) -> dict:
    if not mapping:
        return row
    mapped = {}
    for src_key, value in row.items():
        dest_key = mapping.get(src_key, src_key)
        mapped[dest_key] = value
    return mapped


def _collect_language_fields(row: dict) -> list[dict]:
    languages = []
    for key, value in row.items():
        if key.startswith("lang_"):
            lang_code = key.replace("lang_", "")
            languages.append({"lang_code": lang_code, "value": value})
    return languages


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
    for idx, row in enumerate(reader, start=2):  # header is line 1
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
    _write_error_report(failed)
    return {
        "imported": imported,
        "failed": failed,
        "error_report_url": "/api/terms/import/errors" if failed else None,
    }


def _write_error_report(failed: list[dict]) -> None:
    ERROR_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ERROR_REPORT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["row", "errors"])
        writer.writeheader()
        for item in failed:
            writer.writerow(
                {
                    "row": item.get("row"),
                    "errors": "; ".join(item.get("errors") or []),
                }
            )


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
