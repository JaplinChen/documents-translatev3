"""PPTX API utility functions.

This module contains file validation, extension checking,
and shared constants for PPTX API endpoints.
"""

from __future__ import annotations

SUPPORTED_EXTENSIONS = {".pptx", ".docx", ".xlsx", ".pdf"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}


def get_file_extension(filename: str | None) -> str:
    """Extract file extension from filename."""
    if not filename or "." not in filename:
        return ""
    return "." + filename.lower().split(".")[-1]


def validate_file_type(filename: str | None) -> tuple[bool, str]:
    """Validate uploaded file type.

    Args:
        filename: Name of the uploaded file

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not filename:
        return False, "請選擇檔案"

    ext = get_file_extension(filename)

    if ext in IMAGE_EXTENSIONS:
        return (
            False,
            (
                f"不支援圖片檔案 ({filename})。此工具只支援翻譯 PPTX, DOCX, XLSX 或 PDF "
                "檔案中的文字內容。"
            ),
        )

    if ext not in SUPPORTED_EXTENSIONS:
        return False, f"不支援的檔案格式 ({ext})，支援 .pptx, .docx, .xlsx, .pdf"

    return True, ""

    return True, ""
