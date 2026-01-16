# 內部文件翻譯工具

## 目的
- 內部使用的文件翻譯工具（先支援 DOCX 與 PPTX）
- 自動語言偵測
- 輸出模式：直接翻譯、雙語
- 校正樣式：色彩標示（Correction）

## 不在範圍內（v1）
- 公開對外、計費、多租戶
- 圖片文字辨識（OCR）
- 動畫與轉場

## 快速開始
### 後端
```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

### 前端
```bash
cd frontend
npm install
npm run dev
```

## PPTX 範例指令
- 文字抽取：
```bash
python -m backend.tools.extract_pptx tests/fixtures/sample.pptx > /tmp/blocks.json
```

- 模擬翻譯（雙語）並套用：
```bash
python -m backend.tools.mock_translate_blocks --in /tmp/blocks.json --out /tmp/blocks_translated.json
python -m backend.tools.apply_bilingual --in tests/fixtures/sample.pptx --out /tmp/sample_bilingual.pptx --blocks /tmp/blocks_translated.json
```

- 模擬翻譯（校正）並套用：
```bash
python -m backend.tools.mock_translate_blocks --in /tmp/blocks.json --out /tmp/blocks_corrected.json
python -m backend.tools.apply_corrections --in tests/fixtures/sample.pptx --out /tmp/sample_corrected.pptx --blocks /tmp/blocks_corrected.json
```

## API（PPTX）
- 抽取：`POST /api/pptx/extract`（multipart：file）
- 套用：`POST /api/pptx/apply`（multipart：file, blocks, mode, fill_color, text_color, line_color, line_dash）
- 翻譯：`POST /api/pptx/translate`（multipart：blocks, source_language, target_language, mode）
- 模型清單：`POST /api/llm/models`（multipart：provider, api_key, base_url）

## 語言偵測
- 回傳 `language_summary`（primary/secondary/counts）
- 前端可依此填入來源語言與第二語言

## LLM 設定
- `TRANSLATE_LLM_MODE=real|mock`
  - 預設為 `real`，需要對應供應商的 API Key 或本機服務
  - `mock` 模式會強制使用 MockTranslator，忽略前端傳入的 provider 與連線設定
- `OPENAI_API_KEY`、`OPENAI_MODEL`、`OPENAI_BASE_URL`
- `GEMINI_API_KEY`、`GEMINI_MODEL`、`GEMINI_BASE_URL`
- `LLM_CHUNK_SIZE`、`LLM_MAX_RETRIES`、`LLM_RETRY_BACKOFF`
- `LLM_CONTEXT_STRATEGY=none|neighbor|title-only|deck`
- `LLM_GLOSSARY_PATH=/path/to/glossary.csv`
- Ollama GPU 設定（需由本機 Ollama 支援 GPU）：
  - `OLLAMA_FORCE_GPU=1`（未指定 GPU 參數時，預設使用 `num_gpu=1`）
  - `OLLAMA_NUM_GPU`、`OLLAMA_NUM_GPU_LAYERS`
  - `OLLAMA_NUM_CTX`、`OLLAMA_NUM_THREAD`

## 翻譯記憶庫（SQLite）
- 資料庫位置：`data/translation_memory.db`
- glossary：術語表，優先套用
- tm：翻譯記憶，命中後直接套用

## CSV 匯入格式
- glossary：`source_lang,target_lang,source_text,target_text,priority`
- tm：`source_lang,target_lang,source_text,target_text`

## 限制說明
- 複雜排版與混合字型可能被簡化
- 雙語模式可能讓版面略為重新流動
- 校正樣式以整個圖形為單位，無法精準到每個字元
- 部分形狀不支援逐段落上色

## 驗證指令
- build：`build`
- lint：`lint`
- test：`test`
