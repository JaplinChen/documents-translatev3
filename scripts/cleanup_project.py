import os
import shutil
import argparse
from pathlib import Path

# 配置清理目標 (分類)
TARGETS = {
    "CACHE": [
        "frontend/dist",
        "**/*/__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "**/.DS_Store",
    ],
    "TEMP_ARTIFACTS": [
        "release_package",
        "*.tar",
        "install_log.txt",
        "backend/test_zip_dup.py",
        "backend_logs.txt",
        "data/.update.lock",
        "data/.last_update_hash",
    ],
    "DEBUG_SCRIPTS": [
        "debug_ollama_connection.py",
        "debug_nuclear.py",
        "backend/debug_nuclear.py",
        "probe_contracts.py",
        "probe_flow.py",
        "check_env.py",
        "build.cmd",
    ],
    "ORPHANED_TESTS": [
        "test_api_flow.py",
        "test_final_quality.py",
        "test_regex.py",
    ],
    "LOGS": [
        "*.log",
        "**/*.log",
        "*.tmp",
        "*.bak",
    ]
}

def get_to_delete(project_root):
    to_delete = []
    
    # 處理精確路徑與 glob
    for category, paths in TARGETS.items():
        for pattern in paths:
            if "**/" in pattern:
                # 遞迴搜尋
                p_clean = pattern.replace("**/", "")
                for p in project_root.rglob(p_clean):
                    to_delete.append((p, category))
            elif "*" in pattern:
                # 目錄下的 glob
                for p in project_root.glob(pattern):
                    to_delete.append((p, category))
            else:
                # 精確路徑
                p = project_root / pattern
                if p.exists():
                    to_delete.append((p, category))
    return to_delete

def cleanup(dry_run=True):
    # 腳本位在 scripts/，root 為上一層
    project_root = Path(__file__).parent.parent.absolute()
    all_to_delete = get_to_delete(project_root)

    if not all_to_delete:
        print("Done. No items found to clean.")
        return

    print(f"{' [DRY RUN] ' if dry_run else ' [LIVE RUN] '} Proposed items for removal:")
    print("-" * 50)
    for p, cat in sorted(all_to_delete, key=lambda x: x[1]):
        rel_path = p.relative_to(project_root)
        print(f"[{cat:15}] {rel_path}")
    print("-" * 50)

    if dry_run:
        print("\nNote: This was a dry run. Use --no-dry-run to perform actual deletion.")
        return

    confirm = input("\nAre you sure you want to delete these items? (y/N): ").lower()
    if confirm == 'y':
        for p, _ in all_to_delete:
            try:
                if p.is_dir():
                    shutil.rmtree(p)
                else:
                    p.unlink()
                print(f"Deleted: {p.relative_to(project_root)}")
            except Exception as e:
                print(f"Error deleting {p}: {e}")
        print("\nCleanup cycle completed.")
    else:
        print("\nCleanup aborted by user.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Documents-Translate Codebase Cleanup Tool")
    parser.add_argument("--no-dry-run", action="store_true", help="Perform actual deletion")
    args = parser.parse_args()

    cleanup(dry_run=not args.no_dry_run)
