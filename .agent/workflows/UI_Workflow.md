# UI Operations Master Workflow

這個 workflow 整合了所有 UI/Frontend 相關的開發、修復與優化指令，專注於 React/Vue 與 CSS/Tailwind 生態。

## 可用指令

- `/ui fix` — 安全修正 UI (鎖定 DOM 結構)
- `/ui component` — 生成標準化原子元件 (Atomic Design)
- `/ui responsive` — 響應式適配 (Mobile-First)
- `/ui theme` — 設計系統對齊 (移除 Hardcoded Values)
- `/ui polish` — 視覺動效與互動狀態拋光
- `/ui connect` — 生成前端 API Client (Fetch/Axios)
- `/ui diagram` — 生成架構流程圖 (Mermaid.js)
- `/ui i18n` — 提取硬編碼文字並生成翻譯鍵值

## 指令詳細說明

### 1. 安全修正 (`/ui fix`)

針對現有 UI 進行樣式微調，嚴格禁止破壞結構：

- **結構鎖定 (DOM Lock)**：
  - ❌ 禁止新增/刪除 `div`、`span` 或改變巢狀層級（除非必要）。
  - ❌ 禁止修改 `onClick`、`useEffect` 等業務邏輯。

- **樣式應用**：
  - 優先使用專案現有的 Tailwind Classes 或 CSS Variables。
  - 移除 "Magic Numbers" (如 `width: 355px`)。

- **視覺檢查**：確保修改不會造成 Layout Shift 或 Overflow。

### 2. 元件生成 (`/ui component`)

生成符合 Atomic Design 的可複用元件：

- **介面定義**：優先定義 TypeScript Props (含 `className`, `children`)。
- **原子化原則**：
  - 保持 Stateless (純展示元件)，除非指定包含邏輯。
  - 隔離外部依賴，確保獨立性。
- **無障礙 (A11y)**：自動加入 `aria-label`、`role` 等屬性。

### 3. 響應式適配 (`/ui responsive`)

修正或實作 RWD (Mobile/Tablet/Desktop)：

- **Mobile First**：預設樣式為手機版，使用 `md:`, `lg:` 覆寫大螢幕樣式。
- **佈局轉換**：
  - 將固定 `px` 寬度轉換為 `%`, `flex`, 或 `grid`。
  - 處理水平溢位 (Horizontal Overflow)。
- **觸控友善**：確保手機版按鈕/連結至少 44x44px。

### 4. 主題對齊 (`/ui theme`)

消除硬編碼樣式，對齊 Design System：

- **掃描**：找出所有 Hex Code (`#F00`)、固定像素 (`16px`)。
- **映射**：
  - `#EF4444` -> `text-red-500` 或 `var(--color-error)`。
  - `padding: 20px` -> `p-5` 或 `var(--spacing-xl)`。
- **重構**：替換為標準變數。

### 5. 視覺拋光 (`/ui polish`)

提升 UI 質感與互動回饋：

- **互動狀態**：補全 `:hover`, `:active`, `:focus-visible` 樣式。
- **微動畫**：加入 `transition-all` 讓顏色/變形平滑過渡。
- **深度感**：使用 `box-shadow` 取代純平面設計，調整圓角一致性。

### 6. API 對接 (`/ui connect`)

根據後端定義生成前端請求代碼：

- **分析**：讀取後端 Route (URL, Method, Params, Response)。
- **生成**：
  - TypeScript Interface (Request/Response DTO)。
  - Async Function (使用 `fetch` 或 `axios`)。
- **錯誤處理**：統一包裝 Try/Catch 與錯誤回傳型別。

### 7. 架構圖 (`/ui diagram`)

視覺化程式碼邏輯 (Mermaid.js)：

- **模式選擇**：
  - Flowchart (`graph TD`)：複雜判斷邏輯。
  - Sequence (`sequenceDiagram`)：API 呼叫與模組互動。
  - Class (`classDiagram`)：資料模型結構。
- **生成**：產出 Markdown 兼容的 Mermaid 代碼塊。

### 8. 國際化 (`/ui i18n`)

提取介面文字以支援多語系：

- **掃描**：找出所有使用者可見字串 (`innerText`, `placeholder`, error msg)。
- **提取**：替換為 `t('key.path')` 函數呼叫。
- **生成鍵值**：產出 JSON 結構的翻譯檔片段 (zh-TW / en-US)。

## 執行原則 (Agent Rules)

- **Atomic First**: 不要為了改一個按鈕而重寫整個頁面。
- **No Logic Break**: 前端樣式修改絕不能影響資料流 (Data Flow)。
