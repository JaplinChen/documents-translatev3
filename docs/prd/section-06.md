# 6. 資料模型（概念）
### 6.1 Term
- id
- term
- category_id
- status
- case_rule
- note
- created_by
- created_at
- updated_at

### 6.2 TermLanguage
- id
- term_id
- lang_code
- value

### 6.3 TermAlias
- id
- term_id
- alias

### 6.4 Category
- id
- name
- sort_order

### 6.5 TermVersion
- id
- term_id
- diff
- created_by
- created_at
