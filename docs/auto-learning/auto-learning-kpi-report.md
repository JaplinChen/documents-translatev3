# KPI 與告警報表範本

本文件提供 KPI 欄位、計算方式與報表輸出範本，並列出告警門檻。

## KPI 欄位定義
- `tm_hit_rate`：TM 命中次數 / 全部翻譯查詢次數
- `glossary_hit_rate`：Glossary 命中次數 / 全部翻譯查詢次數
- `overwrite_rate`：覆寫次數 / 命中次數
- `auto_promotion_error_rate`：抽樣錯誤升級數 / 抽樣升級數
- `wrong_suggestion_rate`：抽樣錯誤建議數 / 抽樣建議數

## 計算窗口
- 日統計：`stat_date` 為 UTC 日期
- 移動平均：7 日、30 日
- 需同時輸出 scope 維度（scope_type、scope_id）

## 報表輸出欄位（CSV）
```text
stat_date,scope_type,scope_id,tm_hit_rate,glossary_hit_rate,overwrite_rate,auto_promotion_error_rate,wrong_suggestion_rate
```

## KPI 預設門檻
- TM 命中率 >= 20%（上線 4 週後）
- Glossary 命中率 >= 5%
- 覆寫率 <= 8%（7 日移動平均）
- 自動升級錯誤率 <= 3%（抽樣）
- 錯誤建議率 <= 5%（抽樣）

## 告警規則
- 連續 3 天 TM 命中率 < 15% -> 降低升級門檻並啟用影子模式
- 7 日覆寫率 > 12% -> 自動降級 Glossary -> TM
- 7 日錯誤建議率 > 8% -> 暫停自動升級

## 取樣與抽查建議
- 每日固定抽樣 200 筆或 1%（取較大者）
- 抽樣需涵蓋多語系與多 scope
- 抽樣結果回寫 learning_events 以利追蹤
