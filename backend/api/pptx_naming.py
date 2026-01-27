from __future__ import annotations

import os
import re
import time
from pathlib import Path

EXPORT_DIR = Path("data/exports")


def _ensure_export_dir() -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    return EXPORT_DIR


def _next_sequence(prefix: str, glob_pattern: str) -> str:
    export_dir = _ensure_export_dir()
    max_sequence = 0
    for path in export_dir.glob(glob_pattern):
        try:
            seq_part = path.stem.replace(prefix, "")
            if seq_part.isdigit():
                max_sequence = max(max_sequence, int(seq_part))
        except (ValueError, IndexError):
            continue
    return f"{max_sequence + 1:03d}"


def _sanitize_base(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def _build_pattern(original_filename: str, mode: str, layout: str) -> str:
    base_name, _ = os.path.splitext(original_filename or "output.pptx")
    safe_base = _sanitize_base(base_name)
    date_str = time.strftime("%Y%m%d")
    layout_label = layout if mode == "bilingual" else "none"
    return f"{safe_base}-{mode}-{layout_label}-{date_str}-"


def get_next_sequence(base_pattern: str) -> str:
    return _next_sequence(base_pattern, f"{base_pattern}*.pptx")


def get_next_sequence_with_ext(base_pattern: str, extension: str) -> str:
    ext = extension if extension.startswith(".") else f".{extension}"
    return _next_sequence(base_pattern, f"{base_pattern}*{ext}")


def generate_semantic_filename(
    original_filename: str,
    mode: str,
    layout: str,
) -> str:
    pattern = _build_pattern(original_filename, mode, layout)
    sequence = get_next_sequence(pattern)
    return f"{pattern}{sequence}.pptx"


def generate_semantic_filename_with_ext(
    original_filename: str,
    mode: str,
    layout: str,
    extension: str,
) -> str:
    pattern = _build_pattern(original_filename, mode, layout)
    sequence = get_next_sequence_with_ext(pattern, extension)
    ext = extension if extension.startswith(".") else f".{extension}"
    return f"{pattern}{sequence}{ext}"
