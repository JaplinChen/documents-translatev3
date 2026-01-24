import os
import time
import re
from pathlib import Path

def get_next_sequence(base_pattern: str) -> str:
    export_dir = Path("data/exports")
    export_dir.mkdir(parents=True, exist_ok=True)
    existing_files = list(export_dir.glob(f"{base_pattern}*.pptx"))
    max_seq = 0
    for f in existing_files:
        try:
            name_part = f.stem
            seq_str = name_part.replace(base_pattern, "")
            if seq_str.isdigit(): max_seq = max(max_seq, int(seq_str))
        except (ValueError, IndexError): continue
    return f"{max_seq + 1:03d}"

def get_next_sequence_with_ext(base_pattern: str, extension: str) -> str:
    export_dir = Path("data/exports")
    export_dir.mkdir(parents=True, exist_ok=True)
    ext = extension if extension.startswith(".") else f".{extension}"
    existing_files = list(export_dir.glob(f"{base_pattern}*{ext}"))
    max_seq = 0
    for f in existing_files:
        try:
            name_part = f.stem
            seq_str = name_part.replace(base_pattern, "")
            if seq_str.isdigit():
                max_seq = max(max_seq, int(seq_str))
        except (ValueError, IndexError):
            continue
    return f"{max_seq + 1:03d}"

def generate_semantic_filename(original_filename: str, mode: str, layout: str) -> str:
    base_name, _ = os.path.splitext(original_filename or "output.pptx")
    safe_base = re.sub(r'[\\/*?:"<>|]', "_", base_name)
    date_str = time.strftime("%Y%m%d")
    mode_label = mode
    layout_label = layout if mode == "bilingual" else "none"
    pattern = f"{safe_base}-{mode_label}-{layout_label}-{date_str}-"
    sequence = get_next_sequence(pattern)
    return f"{pattern}{sequence}.pptx"

def generate_semantic_filename_with_ext(
    original_filename: str,
    mode: str,
    layout: str,
    extension: str,
) -> str:
    base_name, _ = os.path.splitext(original_filename or f"output{extension}")
    safe_base = re.sub(r'[\\/*?:"<>|]', "_", base_name)
    date_str = time.strftime("%Y%m%d")
    mode_label = mode
    layout_label = layout if mode == "bilingual" else "none"
    pattern = f"{safe_base}-{mode_label}-{layout_label}-{date_str}-"
    sequence = get_next_sequence_with_ext(pattern, extension)
    ext = extension if extension.startswith(".") else f".{extension}"
    return f"{pattern}{sequence}{ext}"
