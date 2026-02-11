from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.main import app


def generate_report(output_path: Path) -> None:
    schema = app.openapi()
    paths = schema.get("paths", {})
    layout_paths = {k: v for k, v in paths.items() if k.startswith("/api/layouts")}

    lines: list[str] = []
    lines.append("# Layouts API Contract 檢測報告")
    lines.append("")
    lines.append("## 摘要")
    lines.append(f"- 端點數量：{len(layout_paths)}")
    lines.append("- 本報告由本地 OpenAPI 自動產生。")
    lines.append("")
    lines.append("## 端點清單")
    for path, methods in sorted(layout_paths.items()):
        method_names = ", ".join(sorted(methods.keys()))
        lines.append(f"- `{path}`: `{method_names}`")

    lines.append("")
    lines.append("## 主要欄位基線")
    lines.append("- `GET /api/layouts` 回傳 `layouts[]`，每項至少包含：")
    lines.append("  - `id`, `name`, `file_type`, `modes`, `apply_value`, `enabled`, `is_custom`, `params_schema`")
    lines.append("- `POST /api/layouts/custom/import-preview` 回傳至少包含：")
    lines.append("  - `status`, `received`, `valid`, `skipped`, `created`, `updated`, `unchanged`, `replace_scope_existing`, `details`")
    lines.append("- `details[]` 每項至少包含：")
    lines.append("  - `file_type`, `id`, `key`, `action`, `name`, `changed_fields`")
    lines.append("")
    lines.append("## 風險提醒")
    lines.append("- 若調整欄位命名，需同步更新前端型別與 contract 測試。")
    lines.append("- `details` 回傳上限預設 50 筆，超量資料依賴前端篩選與分頁。")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    generate_report(Path("reports/layouts_api_contract_report.md"))
    print("reports/layouts_api_contract_report.md")
