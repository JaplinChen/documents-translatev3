from __future__ import annotations

from .export_formatters import (
    export_to_docx,
    export_to_md,
    export_to_txt,
    export_to_xlsx,
)
from .export_pdf import export_to_pdf


def get_export_formats() -> list[dict]:
    return [
        {
            "id": "pptx",
            "label": "PowerPoint (.pptx)",
            "icon": "📊",
            "available": True,
        },
        {
            "id": "docx",
            "label": "Word 對照表 (.docx)",
            "icon": "📝",
            "available": True,
        },
        {
            "id": "xlsx",
            "label": "Excel 對照表 (.xlsx)",
            "icon": "📈",
            "available": True,
        },
        {
            "id": "txt",
            "label": "純文字 (.txt)",
            "icon": "📄",
            "available": True,
        },
        {
            "id": "md",
            "label": "Markdown 對照表 (.md)",
            "icon": "🧾",
            "available": True,
        },
    ]
