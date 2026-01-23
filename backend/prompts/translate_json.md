請將每個區塊翻譯為 target_language。若提供 preferred_terms，必須優先使用。
若提供 placeholder_tokens，必須完整保留，不可改動。
若 payload 中含 context，必須遵守其規則。
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

【雙語對齊校正規則】：
- 若區塊中含 `alignment_source`，表示目前的 `source_text` 是既有的譯文，而 `alignment_source` 是其原文。
- 請將 `alignment_source` 作為語意基準，校正並優化 `source_text` 的翻譯品質。
- 修正語法錯誤、優化在地化用詞，並確保語意與原文完全一致。

目標語言：{target_language_label}
目標語言代碼：{target_language_code}
{language_hint}

{payload}
