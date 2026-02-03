# 14. API 清單（建議）
### 14.1 術語
- GET /api/terms
  - 參數：q, category_id, status, has_alias, missing_lang, created_by, date_from, date_to, page, page_size
- POST /api/terms
- GET /api/terms/{id}
- PUT /api/terms/{id}
- DELETE /api/terms/{id}

### 14.2 語言內容
- GET /api/terms/{id}/languages
- PUT /api/terms/{id}/languages

### 14.3 別名
- GET /api/terms/{id}/aliases
- PUT /api/terms/{id}/aliases

### 14.4 分類
- GET /api/categories
- POST /api/categories
- PUT /api/categories/{id}
- DELETE /api/categories/{id}
- PUT /api/categories/sort

### 14.5 匯入/匯出
- POST /api/terms/import
  - 支援：欄位映射、預覽模式
- GET /api/terms/import/{id}/result
- GET /api/terms/export

### 14.6 批次作業
- POST /api/terms/batch
  - body: ids, action, payload

### 14.7 版本紀錄
- GET /api/terms/{id}/versions
- GET /api/terms/{id}/versions/{version_id}
- POST /api/terms/{id}/versions/compare
