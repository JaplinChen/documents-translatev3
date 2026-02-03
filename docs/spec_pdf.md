# PDF 翻譯規格

## 1. 目標
對 PDF 文件進行文字擷取與翻譯。由於 PDF 結構固定且不可流動，初期以「雙語對照」或「文字替換」為目標。

## 2. 範圍
- **文字塊 (Text Blocks)**：使用座標 (x, y, w, h) 擷取文字訊息。
- **分頁 (Pages)**：按頁碼順序處理。
- **匯出格式**：
    - 雙語對照 PDF（新增頁面或在原位標註）。
    - 結構化 Markdown 匯出。

## 3. 資料模型
- `page_index`: 頁碼 (0-based)
- `block_type`: `pdf_text_block`
- `source_text`: 擷取到的文字
- `x, y, width, height`: 文字位置（Points）

## 4. 品質要求
- 必須保留原始閱讀順序（Reading Order）。
- 遇到加密或掃描檔 (Image-only) 需標註不支援或建議先執行 OCR。

## 5. OCR 設定
- 預設引擎：Tesseract
- 允許 PaddleOCR（需額外安裝 `requirements-ocr-paddle.txt`）
- 環境變數：
  - `PDF_OCR_ENGINE`: `tesseract` 或 `paddle`
  - `PDF_OCR_ALLOW_PADDLE`: `1` 才允許自動選用 PaddleOCR
  - `PDF_OCR_PADDLE_FALLBACK`: `1` 允許 Tesseract 低信心時改用 PaddleOCR
  - `PDF_OCR_DPI`、`PDF_OCR_LANG`、`PDF_OCR_CONF_MIN`、`PDF_OCR_PSM`
