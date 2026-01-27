from __future__ import annotations

import json
from collections.abc import Iterable

from backend.services.prompt_store import render_prompt
from backend.services.translate_config import (
    get_language_example as _language_example,
    get_language_hint as _language_hint,
    get_language_label as _language_label,
)

def build_prompt(
    blocks: Iterable[dict],
    target_language: str,
    contract_example: dict,
    context: dict | None,
    preferred_terms: list[tuple[str, str]] | None = None,
    placeholder_tokens: list[str] | None = None,
    language_hint: str | None = None,
    mode: str = "direct",
) -> str:
    input_payload = {
        "target_language": target_language,
        "mode": mode,
        "blocks": list(blocks),
        "contract_schema_example": contract_example,
    }
    if preferred_terms:
        input_payload["preferred_terms"] = [
            {"source": source, "target": target}
            for source, target in preferred_terms
        ]
    if placeholder_tokens:
        input_payload["placeholder_tokens"] = placeholder_tokens
    if context:
        input_payload["context"] = context
    payload = json.dumps(input_payload, ensure_ascii=False)

    # Merge static hint (from map) and dynamic hint (from args)
    static_hint = _language_hint(target_language)
    combined_hint = f"{static_hint}\n{language_hint or ''}".strip()

    try:
        return render_prompt(
            "translate_json",
            {
                "payload": payload,
                "language_hint": combined_hint,
                "language_example": _language_example(target_language),
                "target_language_label": _language_label(target_language),
                "target_language_code": target_language,
            },
        )
    except FileNotFoundError:
        return f"""請將每個區塊翻譯為 target_language。若提供 preferred_terms，必須優先使用。
  若提供 placeholder_tokens，必須完整保留，不可改動。
  若 payload 中含 context，必須遵守其規則。
  若區塊中含 alignment_source，表示目前的 source_text 是既有的譯文，而 alignment_source 是其原文。
  請將 alignment_source 作為語意基準，校正並優化 source_text 的翻譯品質。
  輸出需符合 contract_schema_example 的 JSON，且只輸出 JSON。

  【重要】表格翻譯規則：
  - 表格內容必須保持原有結構，每個儲存格的翻譯需與原文位置對應
  - 表格標題（表頭）應準確翻譯，保持術語一致性
  - 若同一表格中出現相同的專有名詞，必須使用相同的翻譯
  - 避免破壞表格的對齊與格式

  【術語一致性規則】：
  - 若提供 preferred_terms（術語表），必須嚴格遵守
  - 同一文件中相同術語必須維持一致的翻譯
  - 若術語表中的翻譯與上下文不完全相符，請以術語表為準

  目標語言：{_language_label(target_language)}
  目標語言代碼：{target_language}

  {_language_hint(target_language)}

  {payload}"""
