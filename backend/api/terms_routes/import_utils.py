from __future__ import annotations

import csv
from pathlib import Path


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


def _write_error_report(path: Path, failed: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["row", "errors"])
        writer.writeheader()
        for item in failed:
            writer.writerow(
                {
                    "row": item.get("row"),
                    "errors": "; ".join(item.get("errors") or []),
                }
            )
