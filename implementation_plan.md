# 整合 Anthropic Skills 與擴充多格式支援改善計畫

## 背景與前提假設
本計畫旨在將 Anthropic 提供的 PPTX, DOCX, XLSX, PDF 處理最佳實踐（Skills）應用於目前的 `documents-translatev3`（前身為 `PPTX-Translate`）專案中，並新增對 PDF 與 Excel (.xlsx) 的翻譯支援。
專案目前已具備 `pptx` 與 `docx` 的基本架構，後端使用 FastAPI，服務層採用模組化設計。

## 架構與技術選型建議
1.  **模組化擴充**：在 `backend/services/` 下新增 `pdf/` 與 `xlsx/` 目錄，遵循現有的 `extract.py` 與 `apply.py` 模式。
2.  **統一區塊模型**：繼續使用 `backend.contracts.make_block` 產出的標準化 JSON 結構，確保前端預覽與編輯邏輯的一致性。
3.  **核心依賴**：
    *   **XLSX**: 使用 `openpyxl`（與 Skill 建議一致）進行精確的儲存格樣式與內容處理。
    *   **PDF**: 使用 `PyMuPDF` (fitz) 或 `pdfplumber` 進行文字擷取。針對 PDF，實作「文字替換」難度較高（PDF 非流式佈局），初期建議支援「內容擷取與純文字對照翻譯」。
    *   **Anthropic Skills 整合**: 引入 Skill 中關於「結構化內容擷取」與「樣式保留」的啟發式演算法（Heuristics），優化 PPTX 與 DOCX 的現有實作。

## 選項比較表

| 維度 | 方案 A：全面重構（以 Skill 為核心） | 方案 B：漸進式整合（保留現有架構，擴充功能） |
| :--- | :--- | :--- |
| **開發難度** | 高。需大幅更動 API 與現有前端邏輯 | **低**。現有架構已穩定，只需新增服務與 API 端點 |
| **維運複雜度** | 高。需重新驗證所有文件類型 | **低**。各模組解耦，不影響現有 PPTX/DOCX 流程 |
| **安全性** | 需重新評估文件解析安全性 | **高**。繼承現有安全篩選邏輯（如 `_is_numeric_only`） |
| **建議與理由** | 不建議。風險較大。 | **推薦**。最符合 IT 經理對「穩定性」與「技術債控管」的要求。 |

## 分階段實作計畫

### 第一階段：基礎模組建立 (POC)
- [ ] 1. 新增 `backend/services/xlsx/` 與 `backend/services/pdf/`。
- [ ] 2. 在 `xlsx` 中實作 `extract.py`：遍歷 Worksheet 與 Cell，轉換為標準 `block` 矩陣。
- [ ] 3. 在 `pdf` 中實作 `extract.py`：使用 `PyMuPDF` 擷取具備座標資訊的文字區塊。

### 第二階段：API 端點與前端適配 (試點)
- [ ] 4. 擴充 `backend/main.py` 或 `api/` 下的路由，支援新副檔名的上傳與解析。
- [ ] 5. 更新前端 `FileStore` 與 UI，允許選擇 XLSX 與 PDF 檔案。

### 第三階段：效能優化與 Skill 整合 (全功能)
- [ ] 6. 將 Skill 中的 `xlsx` 樣式保護邏輯移植到 `apply.py`。
- [ ] 7. 針對 PDF 提供「雙語 PDF」或「Markdown 匯出」選項。

## 風險與緩解措施
- **PDF 佈局破壞**：PDF 替換文字難以完美保留排版。**緩解**：初期僅提供 Side-by-side 對照表，不強制回寫原 PDF 布局。
- **Excel 效能瓶頸**：大型活頁簿解析緩慢。**緩解**：使用 `openpyxl` 的 `read_only` 模式，並實作分頁（Sheet-by-sheet）擷取。
