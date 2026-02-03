# 19. API Request/Response 範例
### 19.1 建立術語
**Request**
```json
{
  "term": "SSO",
  "category_id": "c_10",
  "status": "active",
  "case_rule": "preserve",
  "note": "企業常用驗證",
  "languages": [
    { "lang_code": "zh-TW", "value": "單一登入" },
    { "lang_code": "en", "value": "Single Sign-On" }
  ],
  "aliases": ["單點登入", "單一簽入"]
}
```

**Response**
```json
{
  "success": true,
  "data": {
    "id": "t_123",
    "message": "created"
  }
}
```

### 19.2 取得術語列表
**Request**
```
GET /api/terms?q=SSO&status=active&page=1&page_size=20
```

**Response**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "t_123",
        "term": "SSO",
        "category_id": "c_10",
        "status": "active",
        "case_rule": "preserve",
        "languages": [
          { "lang_code": "zh-TW", "value": "單一登入" },
          { "lang_code": "en", "value": "Single Sign-On" }
        ],
        "aliases": ["單點登入"],
        "updated_at": "2026-01-28T10:12:00Z"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total_items": 138,
    "total_pages": 7
  }
}
```

### 19.3 批次更新狀態
**Request**
```json
{
  "ids": ["t_123", "t_456"],
  "action": "set_status",
  "payload": { "status": "inactive" }
}
```

**Response**
```json
{
  "success": true,
  "data": { "updated": 2 }
}
```

### 19.4 版本差異比對
**Request**
```json
{
  "version_id_a": "v_001",
  "version_id_b": "v_003"
}
```

**Response**
```json
{
  "success": true,
  "data": {
    "diff": [
      { "field": "note", "from": "企業常用驗證", "to": "企業 SSO" },
      { "field": "languages.en", "from": "Single Sign-On", "to": "SSO" }
    ]
  }
}
```
