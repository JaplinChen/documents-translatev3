# 17.8 回應格式範例
### 17.8.1 成功回應
```json
{
  "success": true,
  "data": {
    "id": "t_123",
    "message": "ok"
  }
}
```

### 17.8.2 失敗回應（單一錯誤）
```json
{
  "success": false,
  "error": {
    "code": "TERM-001",
    "message": "術語重複",
    "details": {
      "field": "term",
      "value": "SSO"
    }
  }
}
```

### 17.8.3 失敗回應（多筆匯入錯誤）
```json
{
  "success": false,
  "error": {
    "code": "CSV-002",
    "message": "欄位值格式錯誤",
    "details": {
      "row_errors": [
        { "row": 2, "field": "status", "value": "enable", "reason": "不支援的狀態值" },
        { "row": 5, "field": "lang_zh-TW", "value": 123, "reason": "內容格式不合法" }
      ]
    }
  }
}
```
