#!/usr/bin/env python3
"""
專案清理腳本 - Codebase Cleanup Script

此腳本用於清理專案中的快取、暫存檔案與建置產出。
預設啟用 DRY-RUN 模式，僅列出將被刪除的項目而不實際刪除。

使用方式:
    python scripts/cleanup_project.py           # Dry-run 模式 (預覽)
    python scripts/cleanup_project.py --execute # 實際執行刪除

作者: Automated by Codebase Cleanup Audit
日期: 2026-01-16
"""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path
from typing import Callable


# 專案根目錄
PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ============================================================
# 要清理的項目定義
# ============================================================

# [CACHE] 快取目錄名稱 - 可安全刪除
CACHE_DIR_NAMES: set[str] = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

# [CACHE] 建置產出目錄 - 相對於專案根目錄的路徑
BUILD_DIRS: list[str] = [
    "frontend/dist",
]

# [TEMP] 暫存檔案模式
TEMP_FILE_PATTERNS: list[tuple[str, str]] = [
    ("*.log", "Log 檔案"),
    ("*.tmp", "暫存檔"),
    ("*.bak", "備份檔"),
    (".DS_Store", "macOS 系統檔案"),
]

# [TEMP] 暫存目錄 - 相對於專案根目錄的路徑
TEMP_DIRS: list[str] = [
    # "tmp",  # 註解掉：可能包含使用者的測試資料，需手動清理
]

# 排除的目錄（不進入這些目錄進行掃描）
EXCLUDED_DIRS: set[str] = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    ".codex",
}


# ============================================================
# 清理函數
# ============================================================


def find_items(
    root: Path,
    condition: Callable[[Path], bool],
    *,
    follow_symlinks: bool = False,
) -> list[Path]:
    """遞迴搜尋符合條件的項目。"""
    found: list[Path] = []

    def should_skip_dir(path: Path) -> bool:
        return path.name in EXCLUDED_DIRS

    for entry in root.iterdir():
        if entry.is_symlink() and not follow_symlinks:
            continue

        if entry.is_dir():
            if should_skip_dir(entry):
                continue
            if condition(entry):
                found.append(entry)
            else:
                found.extend(find_items(entry, condition))
        elif entry.is_file() and condition(entry):
            found.append(entry)

    return found


def find_cache_dirs(root: Path) -> list[Path]:
    """找出所有快取目錄。"""
    return find_items(root, lambda p: p.is_dir() and p.name in CACHE_DIR_NAMES)


def find_temp_files(root: Path) -> list[Path]:
    """找出所有暫存檔案。"""
    results: list[Path] = []
    for pattern, _ in TEMP_FILE_PATTERNS:
        if pattern.startswith("*."):
            # 擴展名模式
            ext = pattern[1:]  # ".log"
            results.extend(
                find_items(root, lambda p, e=ext: p.is_file() and p.suffix == e)
            )
        else:
            # 完整檔名模式
            results.extend(
                find_items(root, lambda p, name=pattern: p.is_file() and p.name == name)
            )
    return results


def get_build_dirs(root: Path) -> list[Path]:
    """取得要清理的建置目錄。"""
    return [root / d for d in BUILD_DIRS if (root / d).exists()]


def get_temp_dirs(root: Path) -> list[Path]:
    """取得要清理的暫存目錄。"""
    return [root / d for d in TEMP_DIRS if (root / d).exists()]


def format_size(size_bytes: int) -> str:
    """格式化檔案大小。"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def get_total_size(paths: list[Path]) -> int:
    """計算總大小。"""
    total = 0
    for path in paths:
        if path.is_file():
            total += path.stat().st_size
        elif path.is_dir():
            for file in path.rglob("*"):
                if file.is_file():
                    total += file.stat().st_size
    return total


def delete_paths(paths: list[Path], *, dry_run: bool = True) -> int:
    """刪除指定路徑，回傳刪除的項目數量。"""
    deleted = 0
    for path in paths:
        try:
            if dry_run:
                print(f"  [DRY-RUN] 將刪除: {path}")
            else:
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
                print(f"  [已刪除] {path}")
            deleted += 1
        except (OSError, PermissionError) as e:
            print(f"  [錯誤] 無法刪除 {path}: {e}")
    return deleted


# ============================================================
# 主程式
# ============================================================


def main() -> int:
    parser = argparse.ArgumentParser(
        description="專案清理腳本 - 清理快取、暫存檔案與建置產出",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
    python scripts/cleanup_project.py              # 預覽模式 (Dry-run)
    python scripts/cleanup_project.py --execute    # 實際執行刪除
    python scripts/cleanup_project.py --no-confirm # 跳過確認 (適合 CI/CD)
        """,
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="實際執行刪除 (預設為 dry-run 模式)",
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="跳過刪除前的確認提示 (適合 CI/CD)",
    )
    args = parser.parse_args()

    dry_run = not args.execute

    print("=" * 60)
    print("專案清理腳本 - Codebase Cleanup")
    print(f"專案目錄: {PROJECT_ROOT}")
    print(f"執行模式: {'DRY-RUN (預覽)' if dry_run else '實際刪除'}")
    print("=" * 60)
    print()

    # 收集所有要清理的項目
    all_items: dict[str, list[Path]] = {
        "[CACHE] 快取目錄": find_cache_dirs(PROJECT_ROOT),
        "[BUILD] 建置目錄": get_build_dirs(PROJECT_ROOT),
        "[TEMP] 暫存檔案": find_temp_files(PROJECT_ROOT),
        "[TEMP] 暫存目錄": get_temp_dirs(PROJECT_ROOT),
    }

    total_items = 0
    total_size = 0

    for category, items in all_items.items():
        if items:
            size = get_total_size(items)
            total_size += size
            print(f"\n{category} ({len(items)} 項, {format_size(size)}):")
            for item in sorted(items):
                rel_path = item.relative_to(PROJECT_ROOT)
                if item.is_file():
                    file_size = format_size(item.stat().st_size)
                    print(f"  - {rel_path} ({file_size})")
                else:
                    dir_size = format_size(get_total_size([item]))
                    print(f"  - {rel_path}/ ({dir_size})")
            total_items += len(items)

    if total_items == 0:
        print("\n✨ 專案非常乾淨，沒有需要清理的項目！")
        return 0

    print("\n" + "-" * 60)
    print(f"總計: {total_items} 項, 約 {format_size(total_size)}")
    print("-" * 60)

    if dry_run:
        print("\n📋 這是 DRY-RUN 模式，未實際刪除任何檔案。")
        print("   若確認要執行清理，請加上 --execute 參數重新執行。")
        return 0

    # 實際執行模式 - 確認刪除
    if not args.no_confirm:
        print("\n⚠️  警告: 即將刪除上述檔案與目錄！")
        confirm = input("是否確認刪除？請輸入 'YES' 進行確認: ")
        if confirm != "YES":
            print("已取消操作。")
            return 0

    print("\n🗑️  開始清理...")
    deleted_count = 0
    for category, items in all_items.items():
        if items:
            print(f"\n{category}:")
            deleted_count += delete_paths(items, dry_run=False)

    print("\n" + "=" * 60)
    print(f"✅ 清理完成！共刪除 {deleted_count} 個項目")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
