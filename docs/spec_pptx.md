# PPTX 翻譯 MVP 規格（內部工具）

## 1. 目標
建立內部工具，用於翻譯 PPTX，並盡可能保留版面配置。

初期重點：
- 既有 PPTX 輸入
- 文字抽取 → 翻譯 → 套回同一份 PPTX
- 僅供內部使用

## 2. 範圍內（MVP）

### 2.1 支援文字類型
- Text box（包含 placeholder）
- Table cell 文字
- Speaker notes（建議支援）

### 2.2 翻譯模式
- 直接翻譯：以翻譯文字取代原文
- 雙語：輸出格式
  - source_text
  - （空白行）
  - translated_text

### 2.3 樣式與佈局處理（優化）
- **自動字級縮放 (Auto-fit)**：針對翻譯後文字過長的情況，實作啟發式縮放演算法（基於 Anthropic Skill 建議）。
- **色彩標示**：可對整段翻譯文字套用不同字色（用於校正模式）。
- 逐句差異標示不在現階段範圍。

### 2.4 語言處理
- 自動偵測來源語言
- 使用者指定目標語言（例如 en、zh-TW、ja）

## 3. 明確不在範圍（MVP）
- SmartArt
- 圖表（含嵌入式 Excel）
- WordArt / Artistic text
- 圖片中的文字（OCR）
- 動畫與轉場
- 公開對外、計費、多租戶

## 4. 資料模型（抽取結果）

每個抽取區塊必須包含：
- slide_index：整數（0-based）
- shape_id：整數（python-pptx 的 shape.shape_id）
- block_type：textbox | table_cell | notes
- source_text：字串
- translated_text：字串（翻譯前為空字串）
- mode：direct | bilingual

文字格式規則：
- 保留換行符號為 `\n`
- 忽略空白或只含空白的文字區塊

## 5. 處理流程
1. 使用者上傳 PPTX
2. 系統抽取文字區塊
3. 區塊送入 LLM 進行翻譯
4. LLM 回傳符合 `translation_contract_pptx.json` 的 JSON
5. 系統將翻譯內容套回 PPTX
6. 產出輸出 PPTX

## 6. 品質要求
- 投影片數量必須維持不變。
- **佈局保留**：盡可能維持原始座標與寬高，若文字溢出則觸發 Auto-fit 邏輯。
- **巢狀元件**：支援 Group Shape 內的文字抽取與套用。
- 遇到不支援的形狀需安全略過，避免崩潰。

## 7. 已知限制（必須文件化）
- 文字格式（混合字型、runs）可能被簡化
- 色彩標示可能套用於整段文字而非逐句
- 部分複雜版面可能略有重新流動
- 雙語模式下，翻譯色彩可能套用於整個文字區塊
- 校正樣式以形狀或表格為單位，python-pptx 可能無法精準到每一格或每一段

## 8. 完成定義（每個工作包）
- 程式碼可在本地執行
- 至少一個自動化測試
- 文件中提供可執行的範例指令
- 限制需在文件或註解中明確說明
