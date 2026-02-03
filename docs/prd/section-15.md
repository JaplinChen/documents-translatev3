# 15. 欄位字典
### 15.1 Term
- id：術語唯一識別碼
- term：術語本體（正規化後儲存）
- category_id：分類 ID
- status：狀態（active / inactive）
- case_rule：大小寫規則（preserve / uppercase / lowercase）
- note：說明/備註
- created_by：建立者
- created_at：建立時間
- updated_at：更新時間

### 15.2 TermLanguage
- id：語言內容 ID
- term_id：術語 ID
- lang_code：語言代碼（如 zh-TW, en, ja）
- value：語言內容

### 15.3 TermAlias
- id：別名 ID
- term_id：術語 ID
- alias：別名內容

### 15.4 Category
- id：分類 ID
- name：分類名稱
- sort_order：排序值

### 15.5 TermVersion
- id：版本 ID
- term_id：術語 ID
- diff：差異內容（欄位級別）
- created_by：變更人
- created_at：變更時間
