import argparse

# --- Configuration ---
TARGET_DIRS = [
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "build",
    "dist"
]
TARGET_EXTENSIONS = [
    ".log",
    ".tmp",
    ".bak",
    ".DS_Store"
]
# Potentially orphaned scripts at root
POTENTIAL_ORPHANS = [
    "check_db.py",
    "check_env.py",
    "one_time_sync.py",
    "test_lang_speed.py",
    "test_sql_speed.py",
    "test_sync.py",
    "test_tm_filter.py",
    "verify_isolated.py",
    "verify_optimization.py",
    "verify_typo.py",
    "tm_cleanup_automation.py",
    "preserve_terms_dump.txt",
    "xlsx.md",
    "install_log.txt",
    "test_simple.png",
    "Improvement_Report.md"
]

def cleanup(dry_run=True, auto_confirm=False):
    print(f"{'='*20} CODEBASE CLEANUP {'='*20}")
    if dry_run:
        print("[MODE] DRY RUN - No files will be deleted")
    else:
        print("[MODE] LIVE - Files will be deleted")
    
    base_path = Path(__file__).parent.parent.absolute()
    deleted_count = 0
    
    # 1. Clean directories
    print("\nScanning for junk directories...")
    for root, dirs, files in os.walk(base_path):
        for d in dirs:
            if d in TARGET_DIRS:
                dir_path = Path(root) / d
                print(f"[CACHE] {dir_path.relative_to(base_path)}")
                if not dry_run:
                    confirm = 'y' if auto_confirm else input(f"Delete directory {dir_path.name}? (y/N): ")
                    if confirm.lower() == 'y':
                        shutil.rmtree(dir_path)
                        deleted_count += 1

    # 2. Clean temporary files
    print("\nScanning for junk files...")
    for root, dirs, files in os.walk(base_path):
        for f in files:
            if any(f.endswith(ext) for ext in TARGET_EXTENSIONS) or f in POTENTIAL_ORPHANS:
                file_path = Path(root) / f
                # Skip important root files if any wrongly matched
                if f == "requirements.txt" or f == "docker-compose.yml":
                    continue
                
                category = "[TEMP]" if f.endswith(tuple(TARGET_EXTENSIONS)) else "[ORPHAN]"
                print(f"{category} {file_path.relative_to(base_path)}")
                
                if not dry_run:
                    confirm = 'y' if auto_confirm else input(f"Delete file {file_path.name}? (y/N): ")
                    if confirm.lower() == 'y':
                        os.remove(file_path)
                        deleted_count += 1

    print("\n" + "="*50)
    if dry_run:
        print("Dry run finished. Run with --live to perform cleaning.")
    else:
        print(f"Cleanup finished. Total items deleted: {deleted_count}")

import os
import shutil
from pathlib import Path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cleanup codebase")
    parser.add_argument("--live", action="store_true", help="Perform actual deletion")
    parser.add_argument("--yes", action="store_true", help="Auto-confirm all deletions")
    args = parser.parse_args()
    
    cleanup(dry_run=not args.live, auto_confirm=args.yes)
