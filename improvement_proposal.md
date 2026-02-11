# 專案優化與開發路線圖 (Project Improvement Roadmap)

本文件紀錄 `PPTX-translate` 的優化方向、已完成項目與未來規劃。

> [!NOTE]
> 最後更新時間: 2026/01/23 (已整合 XLSX/PDF 基礎支援)
> 目前專案已進入 **V2 穩定期**，核心翻譯引擎、格式保留與基礎 AI 視覺支援已實作完成。

---

## ✅ 已完成項目 (Completed)

### 1. 核心功能與品質 (Core & Quality)

- [x] **CJK 排版優化 (Kinsoku Shori)**: 實作了針對中日韓語系的避頭尾點與空白清理邏輯 (`apply_cjk_line_breaking`)。
- [x] **字體自動適配 (Smart Typography)**:
  - 實作 `font_manager` 統一管理字體對應。
  - 支援字體自動縮放 (`estimate_scale`) 防止文字溢出。
  - 支援 `Font Mapping` 防止 CJK 文字退化為預設字體。
- [x] **樣式完美繼承 (Rich Text Preservation)**: 精確複製原始 Run 屬性 (Bold, Italic, Color, Underline)。
- [x] **智慧術語提取 (Smart Glossary)**: 支援由 AI 自動掃描文件提取術語。
- [x] **翻譯快取 (Caching)**: 實作兩層快取 (Memory + Disk)，大幅節省 API Token。
- [x] **多格式基礎支援 (Multi-Format Support)**: 已新增 XLSX 擷取/套用與 PDF 基礎擷取 (V2.1)。

### 2. 架構重構 (Refactoring)

- [x] **後端服務拆分**: 將文字處理、字體管理拆分為獨立模組 (`font_manager.py`)。
- [x] **Regex 優化**: 全域編譯正規表達式，提升處理效能。
- [x] **前端 Regex 統一**: 建立 `utils/regex.js` 消除重複代碼。
- [x] **DevOps 清理**: 建立自動化清理腳本 (`scripts/cleanup/cleanup_project.py`)。

---

## 🚀 待執行優化建議 (Upcoming Roadmap)

### Priority 1: 使用者體驗升級 (UX & Interactive)

1. **[x] 高保真即時預覽 (High-Fidelity Preview)**
    - **目標**: 在網頁端直接呈現 PPTX 的視覺效果，而非僅顯示文字區塊。
    - **現狀**: "/extract" 已回傳座標與維度，前端 "SlidePreview.jsx" 已實作渲染。

2. **[x] 批次編輯工具 (Batch Operations)**
    - **目標**: 針對大量投影片進行快速修正。
    - **現狀**: 已實作 "BatchReplaceToolbar.jsx"，支援全等、Regex 取代。

### Priority 2: 前端架構現代化 (Frontend Modernization)

1. **[x] 引入狀態管理 (State Management)**
    - **現狀**: 已引入 "Zustand"，狀態分散至 "FileStore", "SettingsStore", "UIStore"。

2. **[x] 單元測試引入 (Frontend Testing)**
    - **現狀**: 已建立 "Vitest" 測試環境，包含 Store 與核心 Hook 的單元測試。

3. **[ ] 虛擬列表 (Virtualization)**
    - **待辦**: 當投影片超過 100 頁時，Editor 列表應採用 "react-window"。

### Priority 3: 進階 AI 應用 (Advanced AI)

1. **[/] 多模態視覺修正 (Vision-based Layout Fix)**
    - **現狀**: 前端設定已增加 "useVision" 開關，後端仍需完成 Vision LLM 對座標修正的回饋整合。

2. **[ ] 風格遷移 (Style Transfer)**
    - **建議**: AI 自動建議配色。

### Priority 4: 運維 (DevOps) [COMPLETED]

1. **[x] 健康檢查與自動修復 (Self-Healing)**
    - **現狀**: 透過 Docker Healthcheck 與 "unless-stopped" 核心達成自動重啟。

2. **[x] CI/CD Pipeline**
    - **現狀**: GitHub Actions 已實作，包含 pytest、npm test、build 驗證。

### Priority 5: 多格式輸出強化 (Multi-Format Export+)

1. **[ ] PDF 完整重構 (Full PDF Reconstruction)**
    - **目標**: 實現將翻譯後的文字直接回填至原 PDF 頁面中，保留視覺佈局。
    - **方案**: 使用 `PyMuPDF` 結合 `reportlab` 在原有的頁面上覆蓋一層透明的翻譯層，或利用 `OCR` 座標。

2. **[ ] Excel 樣式與公式繼承 (XLSX Style & Formula Preservation)**
    - **目標**: 在翻譯後保留儲存格的背景色、邊框、對齊方式與公式。
    - **待辦**: 調整 `apply.py` 段落，使其不僅更新 `cell.value` 而是保留全物件屬性。

3. **[ ] OCR 掃描件處理 (OCR Integration)**
    - **目標**: 支援圖片型 PDF 的翻譯預覽。
    - **方案**: 整合 `Tesseract` 或輕量級 `EasyOCR` 作為預處理管道。

---

> [!TIP]
> 建議優先順序: **XLSX Style Preservation** > **PDF Reconstruction** > **Vision Layout Review**。
> 目前 XLSX 基礎已打好，樣式保留是使用者最迫切的需求。
