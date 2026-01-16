請將每個區塊翻譯為 target_language。若提供 preferred_terms，必須優先使用。
若提供 placeholder_tokens，必須完整保留，不可改動。
若 payload 中含 context，必須遵守其規則。
輸出需符合 contract_schema_example 的 JSON，且只輸出 JSON。

目標語言：{target_language_label}
目標語言代碼：{target_language_code}
{language_hint}

{payload}
