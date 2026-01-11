# Internal Document Translation Tool

Purpose:
- Internal tool for translating office documents (DOCX first)
- Auto language detection
- Output modes:
  - Direct translation
  - Bilingual (source + target)
- Correction styles:
  - Color highlight
  - Strikethrough + corrected text

Non-goals (v1):
- No public access
- No billing
- Image overlay is phase 2

PPTX extraction:
- Install deps: `pip install -r requirements.txt`
- Extract blocks: `python -m backend.tools.extract_pptx tests/fixtures/sample.pptx > /tmp/blocks.json`

PPTX extractor (0-based slide index):
- Run: `python -m backend.tools.extract_pptx tests/fixtures/sample.pptx`

PPTX bilingual apply:
- Mock translate: `python -m backend.tools.mock_translate_blocks --in /tmp/blocks.json --out /tmp/blocks_translated.json`
- Apply: `python -m backend.tools.apply_bilingual --in tests/fixtures/sample.pptx --out /tmp/sample_bilingual.pptx --blocks /tmp/blocks_translated.json`

PPTX 中文校正套色:
- Mock translate: `python -m backend.tools.mock_translate_blocks --in /tmp/blocks.json --out /tmp/blocks_corrected.json`
- Apply: `python -m backend.tools.apply_corrections --in tests/fixtures/sample.pptx --out /tmp/sample_corrected.pptx --blocks /tmp/blocks_corrected.json`

Tests:
- Run all: `python -m unittest discover -s tests`

UI 介面 (React):
- 後端啟動: `uvicorn backend.main:app --reload`
- 前端啟動: `cd frontend && npm install && npm run dev`
- 開啟: `http://localhost:5173`

API (PPTX):
- 抽取: `POST /api/pptx/extract` (multipart: file)
- 套用: `POST /api/pptx/apply` (multipart: file, blocks, mode, fill_color, text_color, line_color, line_dash)
- 翻譯: `POST /api/pptx/translate` (multipart: blocks, source_language, target_language, mode)
- 校正模式會只取來源語言段落送翻譯，輸出用於覆寫第二語言內容
- 模型偵測: `POST /api/llm/models` (multipart: provider, api_key, base_url)

語言偵測:
- 抽取時回傳 `language_summary`（primary/secondary/counts）
- 前端可手動覆寫來源語言與第二語言

LLM 設定:
- 於 UI 右上角「LLM 設定」設定供應商、API Key 與模型
- API Key 僅保存在瀏覽器 localStorage，不會寫入伺服器

翻譯記憶庫（SQLite）:
- DB 位置：`data/translation_memory.db`
- glossary（術語對照）：翻譯前套用
- tm（翻譯記憶）：完整句子命中後直接回傳

CSV 匯入格式:
- glossary: `source_lang,target_lang,source_text,target_text,priority`
- tm: `source_lang,target_lang,source_text,target_text`

LLM 翻譯參數:
- `TRANSLATE_LLM_MODE=mock|real`
- `OPENAI_API_KEY`、`OPENAI_MODEL`、`OPENAI_BASE_URL`
- `LLM_CHUNK_SIZE`、`LLM_MAX_RETRIES`、`LLM_RETRY_BACKOFF`
- `LLM_CONTEXT_STRATEGY=none|neighbor|title-only|deck`
- `LLM_GLOSSARY_PATH=/path/to/glossary.csv`

區塊選取:
- blocks 內加入 `selected: false` 可跳過套用
