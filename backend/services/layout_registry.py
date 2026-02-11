from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any


_LOCK = Lock()
_DATA_DIR = Path("data/layouts")
_CUSTOM_LAYOUTS_PATH = _DATA_DIR / "custom_layouts.json"


def _builtin_layouts() -> list[dict[str, Any]]:
    return [
        {
            "id": "inline",
            "name": "同頁雙語",
            "file_type": "pptx",
            "modes": ["bilingual"],
            "apply_value": "inline",
            "is_custom": False,
            "enabled": True,
            "params_schema": {
                "type": "object",
                "properties": {
                    "separator_style": {
                        "type": "string",
                        "title": "分隔樣式 (linebreak/blank_line/slash)",
                        "default": "blank_line",
                        "enum": ["linebreak", "blank_line", "slash"],
                        "description": "雙語拼接分隔符號。",
                    },
                    "source_first": {
                        "type": "boolean",
                        "title": "原文在前",
                        "default": True,
                        "description": "啟用後以「原文+譯文」順序呈現。",
                    },
                },
                "additionalProperties": False,
            },
        },
        {
            "id": "auto",
            "name": "自動調整",
            "file_type": "pptx",
            "modes": ["bilingual"],
            "apply_value": "auto",
            "is_custom": False,
            "enabled": True,
            "params_schema": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
        {
            "id": "new_slide",
            "name": "新頁面",
            "file_type": "pptx",
            "modes": ["bilingual"],
            "apply_value": "new_slide",
            "is_custom": False,
            "enabled": True,
            "params_schema": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
        {
            "id": "inline",
            "name": "同儲存格換行",
            "file_type": "xlsx",
            "modes": ["bilingual"],
            "apply_value": "inline",
            "is_custom": False,
            "enabled": True,
            "params_schema": {
                "type": "object",
                "properties": {
                    "wrap_text": {
                        "type": "boolean",
                        "title": "自動換行",
                        "default": True,
                        "description": "雙語內容超過欄寬時啟用儲存格換行。",
                    },
                    "colorize_translations": {
                        "type": "boolean",
                        "title": "翻譯文字上色",
                        "default": True,
                        "description": "雙語內容超過欄寬時啟用儲存格換行。",
                    },
                    "skip_numbers": {
                        "type": "boolean",
                        "title": "跳過數字列",
                        "default": False,
                        "description": "不翻譯僅含數字的儲存格。",
                    },
                    "skip_dates": {
                        "type": "boolean",
                        "title": "跳過日期列",
                        "default": False,
                        "description": "不翻譯符合日期格式的內容。",
                    },
                    "skip_code": {
                        "type": "boolean",
                        "title": "跳過代碼列",
                        "default": False,
                        "description": "跳過程式碼、公式或特定代碼格式。",
                    },
                    "skip_translated": {
                        "type": "boolean",
                        "title": "跳過已有譯文的單元格",
                        "default": False,
                        "description": "若單元格已有內容則不再翻譯。",
                    },
                },
                "additionalProperties": False,
            },
        },
        {
            "id": "new_sheet",
            "name": "新工作表",
            "file_type": "xlsx",
            "modes": ["bilingual"],
            "apply_value": "new_sheet",
            "is_custom": False,
            "enabled": True,
            "params_schema": {
                "type": "object",
                "properties": {
                    "colorize_translations": {
                        "type": "boolean",
                        "title": "翻譯文字上色",
                        "default": True,
                        "description": "新工作表中的譯文是否套用藍色。",
                    },
                    "skip_numbers": {
                        "type": "boolean",
                        "title": "跳過數字列",
                        "default": False,
                        "description": "不傳送僅含數字的內容至翻譯引擎。",
                    },
                    "skip_dates": {
                        "type": "boolean",
                        "title": "跳過日期列",
                        "default": False,
                        "description": "忽略日期格式的儲存格。",
                    },
                    "skip_code": {
                        "type": "boolean",
                        "title": "跳過代碼列",
                        "default": False,
                        "description": "不翻譯代碼、組態字串等。",
                    },
                    "skip_translated": {
                        "type": "boolean",
                        "title": "跳過已有譯文的單元格",
                        "default": False,
                        "description": "避免覆蓋已存在的翻譯內容。",
                    },
                },
                "additionalProperties": False,
            },
        },
        {
            "id": "inline",
            "name": "原段落雙語",
            "file_type": "docx",
            "modes": ["bilingual"],
            "apply_value": "inline",
            "is_custom": False,
            "enabled": True,
            "params_schema": {
                "type": "object",
                "properties": {
                    "separator_style": {
                        "type": "string",
                        "title": "分隔樣式 (linebreak/blank_line)",
                        "default": "linebreak",
                        "enum": ["linebreak", "blank_line"],
                        "description": "段落內原文與譯文的分隔方式。",
                    },
                    "colorize_translations": {
                        "type": "boolean",
                        "title": "譯文上色",
                        "default": True,
                        "description": "譯文 run 套用強調色。",
                    },
                },
                "additionalProperties": False,
            },
        },
        {
            "id": "inline",
            "name": "原位置覆蓋",
            "file_type": "pdf",
            "modes": ["bilingual"],
            "apply_value": "inline",
            "is_custom": False,
            "enabled": True,
            "params_schema": {
                "type": "object",
                "properties": {
                    "show_source": {
                        "type": "boolean",
                        "title": "保留原文",
                        "default": True,
                        "description": "關閉後只顯示譯文。",
                    },
                    "separator_style": {
                        "type": "string",
                        "title": "分隔樣式 (linebreak/blank_line/slash)",
                        "default": "linebreak",
                        "enum": ["linebreak", "blank_line", "slash"],
                        "description": "雙語文字在 textbox 內的分隔樣式。",
                    },
                    "source_first": {
                        "type": "boolean",
                        "title": "原文在前",
                        "default": True,
                        "description": "是否先輸出原文再輸出譯文。",
                    },
                    "font_scale": {
                        "type": "number",
                        "title": "字級倍率 (0.5~2.0)",
                        "default": 1.0,
                        "minimum": 0.5,
                        "maximum": 2.0,
                        "step": 0.1,
                        "description": "調整 PDF 寫回時字級倍率。",
                    },
                },
                "additionalProperties": False,
            },
        },
    ]


def _normalize_layout(item: dict[str, Any]) -> dict[str, Any]:
    out = dict(item)
    out["modes"] = out.get("modes") or ["bilingual"]
    out["enabled"] = bool(out.get("enabled", True))
    out["is_custom"] = bool(out.get("is_custom", False))
    out["params_schema"] = out.get("params_schema") or {
        "type": "object",
        "properties": {},
        "additionalProperties": True,
    }
    return out


def _load_custom_layouts() -> list[dict[str, Any]]:
    if not _CUSTOM_LAYOUTS_PATH.exists():
        return []
    try:
        payload = json.loads(_CUSTOM_LAYOUTS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(payload, list):
        return []
    return [_normalize_layout(item) for item in payload if isinstance(item, dict)]


def _save_custom_layouts(layouts: list[dict[str, Any]]) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    _CUSTOM_LAYOUTS_PATH.write_text(
        json.dumps(layouts, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def list_layouts(
    file_type: str | None = None,
    mode: str | None = None,
    include_disabled: bool = False,
) -> list[dict[str, Any]]:
    all_items = [_normalize_layout(item) for item in _builtin_layouts()]
    all_items.extend(_load_custom_layouts())
    result: list[dict[str, Any]] = []
    for item in all_items:
        if not include_disabled and not item.get("enabled", True):
            continue
        if file_type and item.get("file_type") != file_type:
            continue
        modes = item.get("modes") or []
        if mode and modes and mode not in modes:
            continue
        result.append(item)
    return result


def resolve_layout_apply_value(
    layout_id: str | None,
    file_type: str | None,
    mode: str | None,
    fallback_value: str,
) -> str:
    if not layout_id:
        return fallback_value
    candidates = list_layouts(file_type=file_type, mode=mode)
    for item in candidates:
        if item.get("id") == layout_id:
            return str(item.get("apply_value") or fallback_value)
    return fallback_value


def upsert_custom_layout(layout: dict[str, Any]) -> dict[str, Any]:
    data = _normalize_layout(layout)
    data["is_custom"] = True
    if not data.get("id"):
        raise ValueError("layout id 不可為空")
    if not data.get("name"):
        raise ValueError("layout name 不可為空")
    if data.get("file_type") not in {"pptx", "xlsx", "docx", "pdf"}:
        raise ValueError("file_type 不正確")

    with _LOCK:
        current = _load_custom_layouts()
        replaced = False
        for idx, item in enumerate(current):
            if item.get("id") == data["id"] and item.get("file_type") == data["file_type"]:
                current[idx] = data
                replaced = True
                break
        if not replaced:
            current.append(data)
        _save_custom_layouts(current)
    return data


def get_custom_layout(file_type: str, layout_id: str) -> dict[str, Any] | None:
    for item in _load_custom_layouts():
        if item.get("file_type") == file_type and item.get("id") == layout_id:
            return item
    return None


def list_custom_layouts(file_type: str | None = None) -> list[dict[str, Any]]:
    items = _load_custom_layouts()
    if not file_type:
        return items
    return [item for item in items if item.get("file_type") == file_type]


def delete_custom_layout(file_type: str, layout_id: str) -> bool:
    with _LOCK:
        current = _load_custom_layouts()
        kept = [
            item
            for item in current
            if not (item.get("file_type") == file_type and item.get("id") == layout_id)
        ]
        if len(kept) == len(current):
            return False
        _save_custom_layouts(kept)
    return True


def import_custom_layouts(
    layouts: list[dict[str, Any]],
    mode: str = "merge",
    file_type: str | None = None,
    decisions: dict[str, str] | None = None,
) -> dict[str, int]:
    if mode not in {"merge", "replace"}:
        raise ValueError("mode 僅支援 merge 或 replace")

    normalized: list[dict[str, Any]] = []
    for raw in layouts:
        if not isinstance(raw, dict):
            continue
        item = dict(raw)
        if file_type:
            item["file_type"] = file_type
        data = _normalize_layout(item)
        data["is_custom"] = True
        if not data.get("id") or not data.get("name"):
            continue
        if data.get("file_type") not in {"pptx", "xlsx", "docx", "pdf"}:
            continue
        normalized.append(data)

    decisions_map = decisions or {}

    with _LOCK:
        current = _load_custom_layouts()
        if mode == "replace":
            if file_type:
                current = [c for c in current if c.get("file_type") != file_type]
            else:
                current = []

        upserted = 0
        created = 0
        skipped_by_decision = 0
        for data in normalized:
            decision_key = f"{data.get('file_type')}:{data.get('id')}"
            replaced = False
            for idx, item in enumerate(current):
                if item.get("id") == data["id"] and item.get("file_type") == data["file_type"]:
                    if decisions_map.get(decision_key) == "keep_existing":
                        skipped_by_decision += 1
                        replaced = True
                        break
                    current[idx] = data
                    replaced = True
                    break
            if not replaced:
                current.append(data)
                created += 1
            upserted += 1

        _save_custom_layouts(current)

    return {
        "received": len(layouts),
        "upserted": upserted,
        "created": created,
        "skipped_by_decision": skipped_by_decision,
    }


def preview_import_custom_layouts(
    layouts: list[dict[str, Any]],
    mode: str = "merge",
    file_type: str | None = None,
) -> dict[str, Any]:
    if mode not in {"merge", "replace"}:
        raise ValueError("mode 僅支援 merge 或 replace")

    incoming: list[dict[str, Any]] = []
    for raw in layouts:
        if not isinstance(raw, dict):
            continue
        item = dict(raw)
        if file_type:
            item["file_type"] = file_type
        data = _normalize_layout(item)
        data["is_custom"] = True
        if not data.get("id") or not data.get("name"):
            continue
        if data.get("file_type") not in {"pptx", "xlsx", "docx", "pdf"}:
            continue
        incoming.append(data)

    existing = _load_custom_layouts()
    existing_map = {
        (item.get("file_type"), item.get("id")): item
        for item in existing
    }
    existing_count_for_scope = (
        len([e for e in existing if e.get("file_type") == file_type])
        if file_type
        else len(existing)
    )

    created = 0
    updated = 0
    unchanged = 0
    skipped = len(layouts) - len(incoming)
    details: list[dict[str, Any]] = []

    def _changed_fields(old: dict[str, Any], new: dict[str, Any]) -> list[str]:
        tracked = ["name", "apply_value", "enabled", "modes", "params_schema"]
        out: list[str] = []
        for key in tracked:
            if old.get(key) != new.get(key):
                out.append(key)
        return out

    for data in incoming:
        key = (data.get("file_type"), data.get("id"))
        prev = existing_map.get(key)
        if not prev:
            created += 1
            details.append(
                {
                    "file_type": data.get("file_type"),
                    "id": data.get("id"),
                    "key": f"{data.get('file_type')}:{data.get('id')}",
                    "action": "create",
                    "name": data.get("name"),
                    "changed_fields": [],
                }
            )
            continue
        if prev == data:
            unchanged += 1
            details.append(
                {
                    "file_type": data.get("file_type"),
                    "id": data.get("id"),
                    "key": f"{data.get('file_type')}:{data.get('id')}",
                    "action": "unchanged",
                    "name": data.get("name"),
                    "changed_fields": [],
                }
            )
            continue
        updated += 1
        changed_fields = _changed_fields(prev, data)
        details.append(
            {
                "file_type": data.get("file_type"),
                "id": data.get("id"),
                "key": f"{data.get('file_type')}:{data.get('id')}",
                "action": "update",
                "name": data.get("name"),
                "changed_fields": changed_fields,
            }
        )

    replaced_scope_count = existing_count_for_scope if mode == "replace" else 0
    return {
        "received": len(layouts),
        "valid": len(incoming),
        "skipped": skipped,
        "created": created,
        "updated": updated,
        "unchanged": unchanged,
        "replace_scope_existing": replaced_scope_count,
        "details": details[:50],
    }
