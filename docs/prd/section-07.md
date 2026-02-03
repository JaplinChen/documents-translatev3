# 7. CSV 規格與驗證
### 7.1 固定欄位
- 必填：term、category、status
- 選填：aliases、note、case_rule、lang_zh-TW、lang_en、lang_ja（動態語言欄位）

### 7.2 驗證規則
- term 必填，不可重複（忽略大小寫與多空白）
- category 必填；不存在可在匯入流程選擇自動新增
- status 必填；限定值例如：active / inactive
- aliases 不可與其他 term 或 alias 重複
- case_rule 允許：preserve / uppercase / lowercase
- 文字正規化：trim、多空白合併

### 7.3 匯入流程
1) 上傳 CSV
2) 欄位映射
3) 資料預覽（含錯誤提示）
4) 確認匯入
5) 匯入結果報表（含可下載錯誤清單）
