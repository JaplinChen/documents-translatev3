from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run_cmd(cmd: list[str], cwd: Path | None = None) -> None:
    print(f"[RUN] {' '.join(cmd)}")
    subprocess.run(cmd, cwd=str(cwd or ROOT), check=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="一鍵執行 Layouts API contract 檢查。",
    )
    parser.add_argument(
        "--full-tests",
        action="store_true",
        help="額外執行全量 pytest。",
    )
    parser.add_argument(
        "--frontend-build",
        action="store_true",
        help="額外執行前端 build 驗證。",
    )
    args = parser.parse_args()

    run_cmd([sys.executable, "scripts/dev/generate_layouts_contract_report.py"])
    run_cmd(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_layouts_api_contract.py",
            "tests/test_layouts_import_preview.py",
        ]
    )

    if args.full_tests:
        run_cmd([sys.executable, "-m", "pytest", "-q"])

    if args.frontend_build:
        run_cmd(["npm", "run", "build"], cwd=ROOT / "frontend")

    print("[OK] Layouts contract 檢查完成。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

