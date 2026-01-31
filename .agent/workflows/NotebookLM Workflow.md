# NotebookLM Workflow

這個 workflow 讓你可以直接與 Google NotebookLM 互動，獲取基於你上傳文件的精準回答。

## 可用指令

- `/notebooklm query [問題]` — 查詢 NotebookLM 知識庫
- `/notebooklm add [url]` — 新增 notebook 到 library
- `/notebooklm list` — 列出所有已儲存的 notebook
- `/notebooklm auth` — 進行 Google 帳號登入

---

## 指令詳細說明

### 1. 認證 (`/notebooklm auth`)

首次使用前需進行認證：

1. 使用 `browser_subagent` 開啟 <https://notebooklm.google.com>
2. 等待使用者手動完成 Google 登入
3. 登入成功後，瀏覽器 profile 會保存認證狀態
4. 後續操作將自動使用該認證

### 2. 新增 Notebook (`/notebooklm add [url]`)

將 NotebookLM notebook 加入 library：

1. 讀取 `.shared/notebooklm/library.json`（若不存在則建立）
2. 驗證 URL 格式為 `https://notebooklm.google.com/notebook/*`
3. 使用 `browser_subagent` 開啟 notebook，詢問其內容主題
4. 新增記錄到 `library.json`：

   ```json
   {
     "id": "生成的 UUID",
     "name": "從 notebook 標題或使用者輸入取得",
     "url": "notebook URL",
     "topics": ["從 notebook 內容分析得出"],
     "added_at": "ISO 時間戳記"
   }
   ```

### 3. 列出 Notebooks (`/notebooklm list`)

顯示已儲存的所有 notebooks：

1. 讀取 `.shared/notebooklm/library.json`
2. 格式化輸出每個 notebook 的名稱、主題和 URL

### 4. 查詢 (`/notebooklm query [問題]`)

向 NotebookLM 發問並取得回答：

1. 讀取 `library.json` 取得已儲存的 notebooks
2. 根據問題內容自動選擇最相關的 notebook（或詢問使用者）
3. 使用 `browser_subagent` 執行以下步驟：
   - 開啟 notebook URL
   - 找到聊天輸入框（通常是頁面底部的 textarea）
   - 輸入問題
   - 點擊送出按鈕
   - 等待回答出現（監控 DOM 變化）
   - 擷取回答文字
4. 返回 NotebookLM 的回答給使用者

---

## browser_subagent 操作範例

### 查詢操作

```
Task: 在 NotebookLM 頁面發問並取得回答

RecordingName: notebooklm_query

步驟：

1. 開啟 URL: {notebook_url}
2. 等待頁面載入完成
3. 找到聊天輸入框 (textarea 或 contenteditable 元素)
4. 點擊輸入框使其聚焦
5. 輸入問題: "{question}"
6. 按 Enter 或點擊送出按鈕
7. 等待 3-5 秒讓 NotebookLM 生成回答
8. 擷取最新的回答訊息文字
9. 返回回答內容

返回條件：成功擷取到回答文字，或發生錯誤需要報告
```

---

## 資料儲存

所有資料儲存於 `.shared/notebooklm/` 目錄：

```
.shared/notebooklm/
├── library.json     # Notebook 庫（URL、名稱、主題）
└── README.md        # 說明檔案
```

> ⚠️ **安全提醒**：建議在 `.gitignore` 中排除 `.shared/notebooklm/` 目錄，因為它可能包含敏感的 notebook URL。

---

## 限制

- **無對話上下文**：每次查詢都是獨立的，無法參考「上一個回答」
- **需手動登入**：首次需透過 `/notebooklm auth` 手動登入 Google
- **Notebook 需分享**：要查詢的 notebook 必須設為可存取
- **Rate Limits**：NotebookLM 免費版有每日查詢限制
