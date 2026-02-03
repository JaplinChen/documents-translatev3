# 18. API 參數明細表
### 18.1 GET /api/terms
- q：文字搜尋（術語/別名）
- category_id：分類 ID
- status：狀態
- has_alias：是否有別名（true/false）
- missing_lang：缺值語言代碼（如 zh-TW）
- created_by：建立者 ID
- date_from：起始日期（YYYY-MM-DD）
- date_to：結束日期（YYYY-MM-DD）
- page：頁碼
- page_size：每頁筆數

### 18.2 POST /api/terms
- term：術語
- category_id：分類 ID
- status：狀態
- case_rule：大小寫規則
- note：說明/備註
- languages：語言內容陣列
- aliases：別名陣列

### 18.3 PUT /api/terms/{id}
- term：術語
- category_id：分類 ID
- status：狀態
- case_rule：大小寫規則
- note：說明/備註
- languages：語言內容陣列
- aliases：別名陣列

### 18.4 POST /api/terms/import
- file：CSV 檔案
- mapping：欄位映射設定
- preview：是否僅預覽（true/false）

### 18.5 POST /api/terms/batch
- ids：術語 ID 陣列
- action：batch action（set_category / set_status / set_case_rule / delete）
- payload：對應 action 的內容

### 18.6 POST /api/terms/{id}/versions/compare
- version_id_a：版本 A
- version_id_b：版本 B
