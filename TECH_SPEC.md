# 技術規格書 (PRD): documents-translatev3

## 1. 核心架構 (Core Architecture)

本系統採用「前後端分離」的模組化架構，設計目標為企業內部的高安全性文件翻譯控制台。

### 技術棧 (Tech Stack)
- **後端 (Backend)**: Python 3.10+ (FastAPI), Uvicorn, Pydantic V2。
- **前端 (Frontend)**: React 18, Zustand (輕量狀態管理), Tailwind CSS, i18next。
- **資料庫 (Database)**: SQLite (用於術語與翻譯記憶)，容器佈署時掛載於 `/app/data`。
- **文件引擎**: `python-pptx`, `python-docx`, `openpyxl`, `PyMuPDF (fitz)`。

### 核心設計模式
- **Service Factory**: 根據副檔名分發至對應的處理服務程序。
- **State Store (FE)**: 使用 Zustand 分離管理：
    - `useUIStore`: 控管分頁、彈窗、過濾器、Sticky 佈局狀態。
    - `useFileStore`: 控管目前上傳文件的 Block 數據。
    - `useSettingsStore`: 控管 LLM 供應商 (Ollama, Gemini, OpenAI) 配置。
- **Atomic Rendering**: 每個文件區塊 (`BlockCard`) 均為獨立組件，支援非受控編輯模式。

---

## 2. 功能矩陣與使用者流程

### 功能清單
| 功能名稱 | 說明 | 關鍵技術 |
| :--- | :--- | :--- |
| **多格式翻譯** | 支持 PPTX, DOCX, XLSX, PDF | 座標提取與 Re-indexing |
| **智慧校正** | 支援翻譯後的直接編輯與修正 | Uncontrolled contentEditable |
| **術語管理** | 術語與記憶庫的 CRUD 與 CSV 匯入出 | SQLite context-aware hash |
| **引擎切換** | 支援 Ollama (本地), Gemini, OpenAI | Abstract LLM Client Class |

### 使用者流程
1. **上傳**: 前端發送文件至 `/api/{type}/extract`。
2. **提取**: 後端生成 `PPTXBlock` 序列化數據並緩存。
3. **展示**: 前端呈現雙欄對照介面，支援過濾與搜尋。
4. **引擎同步**: 設定 LLM 參數，啟動 `/api/translate` SSE 流式輸出。
5. **儲存/應用**: 修改內容後，呼叫 `/api/{type}/apply` 生成最終文件。

---

## 3. 資料架構 (Data Schema)

### 核心通訊合約: `PPTXBlock` (或稱為 DocumentBlock)
```typescript
interface DocumentBlock {
  _uid: string;            // 唯一識別碼
  slide_index: number;      // 頁碼/分頁索引
  source_text: string;      // 原始文本
  translated_text: string;  // 翻譯後文本
  x: number; y: number;    // 原始渲染座標 (用於 Preview)
  width: number; height: number;
  block_type: "text" | "table" | "note";
}
```

### SQLite Schema (術語庫)
```sql
-- 術語表 (Glossary)
CREATE TABLE glossary (
  id INTEGER PRIMARY KEY,
  source_lang TEXT, target_lang TEXT,
  source_text TEXT, target_text TEXT,
  priority INTEGER DEFAULT 0
);

-- 翻譯記憶 (TM)
CREATE TABLE tm (
  id INTEGER PRIMARY KEY,
  hash TEXT UNIQUE, -- 生成自 source+target+text+context
  source_lang TEXT, target_lang TEXT,
  source_text TEXT, target_text TEXT
);
```

---

## 4. UI/UX 設計規範 (Design Tokens)

- **主色調**: `Slate-900` (背景), `Blue-600` (主操作), `Slate-50` (卡片背景)。
- **Sticky 佈局**: 
    - 術語管理分頁頂部必須固定 (`z-index: 20`) 以確保持續可讀。
- **輸入行為**: 
    - 編輯器應採用 `onBlur` 回寫機制，避免 `onChange` 觸發的反覆渲染導致焦點遺失。

---

## 5. 技術邏輯 (Technical Logic)

### 翻譯 Chunk 分派機制 (Pseudocode)
```python
def dispatch_translate(blocks, glossary):
    # 1. 執行術語預先取代 (Pre-processing)
    for b in blocks:
        b.translated_text = apply_glossary(b.source_text, glossary)
    
    # 2. 獲取 LLM 提示詞 (Prompt Engineering)
    prompt = load_prompt("translate_standard", context=user_config)
    
    # 3. 異步併發請求 (LLM Client)
    responses = await llm.batch_request(blocks, prompt)
    
    # 4. SSE 推送 (Streaming)
    for res in responses:
        yield f"data: {json.dumps(res)}\n\n"
```

### 術語 Hash 校驗 (Context-Aware)
```python
def generate_tm_hash(lang_pair, text, llm_config):
    # 包含模型名稱與 Tone，確保不同設定下的翻譯能被區分
    payload = f"{lang_pair}|{text}|{llm_config.model}"
    return hashlib.sha256(payload.encode()).hexdigest()
```
