from __future__ import annotations

import logging
import os
import re
import time
from pathlib import Path

LOGGER = logging.getLogger(__name__)


def get_history_items() -> list[dict]:
    export_dir = Path("data/exports")
    if not export_dir.exists():
        return []

    pattern = re.compile(r"^(autosave-)?(.*?)(?:\.[^.]+)?$")
    latest_files: dict[str, dict] = {}

    for ext in ("*.pptx", "*.docx", "*.json"):
        for file_path in export_dir.glob(ext):
            try:
                stat = file_path.stat()
                match = pattern.match(file_path.name)
                is_autosave = "autosave" in file_path.name
                base_key = match.group(2) if match else file_path.name
                metadata = {
                    "filename": file_path.name,
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                    "date_str": time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)
                    ),
                    "type": "autosave" if is_autosave else "final",
                }

                if (
                    base_key not in latest_files
                    or metadata["mtime"] > latest_files[base_key]["mtime"]
                ):
                    latest_files[base_key] = metadata
            except Exception as exc:  # pragma: no cover
                LOGGER.debug("Failed to examine %s: %s", file_path, exc)

    return sorted(
        latest_files.values(),
        key=lambda x: x["mtime"],
        reverse=True,
    )


def delete_history_file(filename: str) -> bool:
    export_dir = Path("data/exports")
    file_path = export_dir / filename
    if not file_path.exists():
        return False
    os.remove(file_path)
    return True
