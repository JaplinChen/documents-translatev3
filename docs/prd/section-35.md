# 30. API 回應格式統一規範
- 成功：success=true + data
- 失敗：success=false + error { code, message, details }
- 分頁：data.items + page/page_size/total_items/total_pages
