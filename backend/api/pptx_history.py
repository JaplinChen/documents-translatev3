import os
import time
import re
import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)

def get_history_items() -> list[dict]:
    export_dir = Path("data/exports")
    if not export_dir.exists(): return []
    # Support both .pptx and .docx
    # Updated pattern: Capture (autosave prefix)? (filename part) (extension)
    # This is much more robust than checking every optional mode/layout field
    pattern = re.compile(r"^(autosave-)?(.*?)(?:\.[^.]+)?$")
    latest_files = {}
    
    for ext in ["*.pptx", "*.docx", "*.json"]:
        for f in export_dir.glob(ext):
            try:
                stat = f.stat()
                match = pattern.match(f.name)
                is_autosave = "autosave" in f.name
                base_key = match.group(2) if match else f.name
                
                info = {
                    "filename": f.name,
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                    "date_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
                    "type": "autosave" if is_autosave else "final"
                }
                # Keep latest version per base_key
                if base_key not in latest_files or info["mtime"] > latest_files[base_key]["mtime"]:
                    latest_files[base_key] = info
            except Exception: continue
    return sorted(latest_files.values(), key=lambda x: x["mtime"], reverse=True)
    return sorted(latest_files.values(), key=lambda x: x["mtime"], reverse=True)

def delete_history_file(filename: str) -> bool:
    export_dir = Path("data/exports")
    file_path = export_dir / filename
    if not file_path.exists(): return False
    os.remove(file_path)
    return True
