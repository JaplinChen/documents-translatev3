# 17.10 CSV 匯入結果報表格式
### 17.10.1 成功回應
```json
{
  "success": true,
  "data": {
    "import_id": "imp_20260128_001",
    "total_rows": 120,
    "success_rows": 118,
    "failed_rows": 2,
    "download_error_report": "https://example.com/imports/imp_20260128_001/errors.csv"
  }
}
```

### 17.10.2 失敗回應（含錯誤清單）
```json
{
  "success": false,
  "error": {
    "code": "CSV-002",
    "message": "欄位值格式錯誤",
    "details": {
      "import_id": "imp_20260128_001",
      "row_errors": [
        { "row": 2, "field": "status", "value": "enable", "reason": "不支援的狀態值" },
        { "row": 5, "field": "lang_zh-TW", "value": 123, "reason": "內容格式不合法" }
      ]
    }
  }
}
```
