# 16. 欄位驗證規則表
### 16.1 Term
- term：必填；去除前後空白；多空白合併；不可與其他 term/alias 重複（忽略大小寫與空白）
- category_id：必填；需存在於分類表
- status：必填；限定 active / inactive
- case_rule：選填；限定 preserve / uppercase / lowercase；空值視為 preserve
- note：選填；長度 ≤ 1000

### 16.2 TermLanguage
- lang_code：必填；格式為 BCP-47（如 zh-TW、en）
- value：選填；長度 ≤ 2000

### 16.3 TermAlias
- alias：選填；不可與其他 term/alias 重複（忽略大小寫與空白）

### 16.4 Category
- name：必填；不可重複（忽略大小寫與空白）；長度 ≤ 100
- sort_order：必填；數值整數

### 16.5 CSV 匯入驗證
- term、category、status 必填
- 未知欄位禁止匯入
- 語言欄位必須符合 lang_ 前綴（如 lang_zh-TW）
- 別名以 | 分隔，單筆別名需通過 alias 規則
