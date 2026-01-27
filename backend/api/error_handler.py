"""Unified error handling for API endpoints.

This module provides decorators to standardize error handling across
FastAPI routes.
"""

from __future__ import annotations

import functools
import json
import logging
import traceback
from collections.abc import Callable

from fastapi import HTTPException, UploadFile

from backend.api.pptx_utils import validate_file_type

LOGGER = logging.getLogger(__name__)


def api_error_handler(
    validate_file: bool = True,
    file_type_error_msg: str | None = None,
    read_error_msg: str | None = None,
) -> Callable:
    """
    Decorator to handle common API errors for file upload endpoints.

    Args:
        validate_file: Whether to validate file type
        file_type_error_msg: Custom error message for invalid file type
        read_error_msg: Custom error message for file read errors
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract file from kwargs if present
            file = kwargs.get("file")
            if file and isinstance(file, UploadFile) and validate_file:
                valid, err = validate_file_type(file.filename)
                if not valid:
                    error_msg = file_type_error_msg or err
                    raise HTTPException(status_code=400, detail=error_msg)

                try:
                    # Pre-read the file to validate it
                    await file.read()
                    # Reset file pointer for the actual handler
                    await file.seek(0)
                except Exception as exc:
                    error_msg = read_error_msg or f"{file.filename} 檔案無效"
                    LOGGER.error(
                        "File read error for %s: %s", file.filename, exc
                    )
                    raise HTTPException(
                        status_code=400,
                        detail=error_msg,
                    ) from exc

            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTP exceptions as-is
                raise
            except Exception as exc:
                # Log unexpected errors
                traceback.print_exc()
                LOGGER.error(
                    "Unexpected error in %s: %s", func.__name__, exc
                )
                raise HTTPException(status_code=500, detail="內部伺服器錯誤") from exc

        return wrapper

    return decorator


def validate_json_blocks(blocks_str: str) -> dict:
    """
    Validate and parse blocks JSON string.

    Args:
        blocks_str: JSON string containing blocks data

    Returns:
        Parsed blocks dictionary

    Raises:
        HTTPException: If JSON is invalid or blocks format is wrong
    """
    try:
        from backend.contracts import coerce_blocks

        return coerce_blocks(json.loads(blocks_str))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="資料格式錯誤") from exc
