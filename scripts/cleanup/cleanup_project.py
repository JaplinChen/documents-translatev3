#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


CACHE_DIR_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", "build", "dist"}
TEMP_FILE_NAMES = {".DS_Store"}
TEMP_FILE_SUFFIXES = {".log", ".tmp", ".bak"}

EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
}

SOURCE_EXTS = {".py", ".js", ".jsx", ".ts", ".tsx"}


@dataclass
class OrphanItem:
    path: Path
    reason: str


@dataclass
class DeadCodeItem:
    path: Path
    line_no: int
    preview: str


def _is_under_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def _walk_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirpath_p = Path(dirpath)
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for filename in filenames:
            yield dirpath_p / filename


def _collect_cache_and_temp(root: Path) -> tuple[list[Path], list[Path]]:
    cache_items: list[Path] = []
    temp_items: list[Path] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirpath_p = Path(dirpath)
        filtered = []
        for d in dirnames:
            if d in EXCLUDE_DIRS:
                continue
            if d in CACHE_DIR_NAMES:
                cache_items.append(dirpath_p / d)
                continue
            filtered.append(d)
        dirnames[:] = filtered

        for f in filenames:
            p = dirpath_p / f
            if f in TEMP_FILE_NAMES or p.suffix.lower() in TEMP_FILE_SUFFIXES:
                temp_items.append(p)

    return cache_items, temp_items


def _iter_source_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for p in _walk_files(root):
        if p.suffix.lower() in SOURCE_EXTS:
            if "tests" in p.parts:
                continue
            files.append(p)
    return files


def _collect_imports_python(text: str) -> set[str]:
    imports: set[str] = set()
    for m in re.finditer(r"^\s*import\s+([a-zA-Z0-9_\.]+)", text, re.M):
        imports.add(m.group(1))
    for m in re.finditer(r"^\s*from\s+([a-zA-Z0-9_\.]+)\s+import\s+([a-zA-Z0-9_\.]+)", text, re.M):
        module = m.group(1)
        name = m.group(2)
        imports.add(module)
        imports.add(f"{module}.{name}")
    return imports


def _collect_imports_js(text: str) -> set[str]:
    imports: set[str] = set()
    for m in re.finditer(r"from\s+['\"]([^'\"]+)['\"]", text):
        imports.add(m.group(1))
    for m in re.finditer(r"import\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", text):
        imports.add(m.group(1))
    for m in re.finditer(r"require\(\s*['\"]([^'\"]+)['\"]\s*\)", text):
        imports.add(m.group(1))
    return imports


def _build_import_index(root: Path, files: list[Path]) -> dict[Path, set[str]]:
    index: dict[Path, set[str]] = {}
    for p in files:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            text = ""
        imports: set[str] = set()
        if p.suffix.lower() == ".py":
            imports |= _collect_imports_python(text)
        else:
            imports |= _collect_imports_js(text)
        index[p] = imports
    return index


def _candidate_module_names(path: Path, root: Path) -> set[str]:
    rel = path.resolve().relative_to(root.resolve())
    no_ext = rel.with_suffix("")
    parts = list(no_ext.parts)
    dotted = ".".join(parts)
    return {dotted}


def _resolve_js_import(from_file: Path, spec: str, root: Path) -> set[str]:
    results: set[str] = set()
    if not spec.startswith("."):
        return results
    base = from_file.parent.resolve()
    target = (base / spec).resolve()
    if _is_under_root(target, root):
        try:
            rel = target.relative_to(root.resolve())
        except Exception:
            return results
        results.add(rel.as_posix())
        results.add(rel.with_suffix("").as_posix())
    return results


def _find_orphans(root: Path, files: list[Path]) -> list[OrphanItem]:
    import_index = _build_import_index(root, files)
    python_imports: set[str] = set()
    js_imports: set[str] = set()

    for f, imports in import_index.items():
        if f.suffix.lower() == ".py":
            python_imports |= imports
        else:
            for spec in imports:
                js_imports |= _resolve_js_import(f, spec, root)

    orphans: list[OrphanItem] = []
    for p in files:
        rel = p.resolve().relative_to(root.resolve())
        if p.name in {"main.py", "manage.py"}:
            continue
        if p.suffix.lower() == ".py":
            module_names = _candidate_module_names(p, root)
            if not (module_names & python_imports):
                orphans.append(OrphanItem(p, "0 imports found (heuristic)"))
        else:
            rel_no_ext = rel.with_suffix("").as_posix()
            rel_with_ext = rel.as_posix()
            if rel_no_ext not in js_imports and rel_with_ext not in js_imports:
                orphans.append(OrphanItem(p, "0 imports found (heuristic)"))

    return orphans


def _find_dead_code(files: list[Path]) -> list[DeadCodeItem]:
    items: list[DeadCodeItem] = []
    py_pat = re.compile(r"^\s*#\s*(def|class)\s+\w+")
    js_pat = re.compile(r"^\s*//\s*(function|class)\s+\w+")
    arrow_pat = re.compile(r"^\s*//\s*\w+\s*=\s*\(.*\)\s*=>")

    for p in files:
        try:
            lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, start=1):
            if p.suffix.lower() == ".py" and py_pat.search(line):
                items.append(DeadCodeItem(p, i, line.strip()))
            elif p.suffix.lower() in {".js", ".jsx", ".ts", ".tsx"}:
                if js_pat.search(line) or arrow_pat.search(line):
                    items.append(DeadCodeItem(p, i, line.strip()))

    return items


def _print_list(title: str, items: Iterable[str]) -> None:
    print(title)
    for item in items:
        print(item)
    print("")


def _confirm_delete(path: Path) -> bool:
    answer = input(f"確認刪除：{path}? (y/N) ").strip().lower()
    return answer == "y"


def _delete_path(path: Path, root: Path) -> None:
    if not _is_under_root(path, root):
        print(f"跳過：不在根目錄內 {path}")
        return
    if path.is_dir():
        if _confirm_delete(path):
            shutil.rmtree(path)
            print(f"已刪除資料夾：{path}")
    elif path.exists():
        if _confirm_delete(path):
            path.unlink()
            print(f"已刪除檔案：{path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="專案清理掃描與報告")
    parser.add_argument("--root", default=".", help="專案根目錄")
    parser.add_argument("--apply", action="store_true", help="執行刪除（預設 dry-run）")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print("根目錄不存在")
        return 1

    cache_items, temp_items = _collect_cache_and_temp(root)
    source_files = _iter_source_files(root)
    orphans = _find_orphans(root, source_files)
    deadcodes = _find_dead_code(source_files)

    _print_list("[CACHE]", [str(p) for p in cache_items])
    _print_list("[TEMP]", [str(p) for p in temp_items])
    _print_list("[ORPHAN]", [f"{o.path} | 原因: {o.reason}" for o in orphans])
    _print_list("[DEADCODE]", [f"{d.path}:{d.line_no} | {d.preview}" for d in deadcodes])

    print("摘要")
    print(f"CACHE: {len(cache_items)}")
    print(f"TEMP: {len(temp_items)}")
    print(f"ORPHAN: {len(orphans)}")
    print(f"DEADCODE: {len(deadcodes)}")

    if not args.apply:
        print("dry-run 模式：未執行刪除")
        return 0

    for p in cache_items:
        _delete_path(p, root)
    for p in temp_items:
        _delete_path(p, root)
    for o in orphans:
        _delete_path(o.path, root)

    print("完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
