# 企業常用文件翻譯與校正控制台 (documents-translatev3)

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-內部使用-lightgrey.svg)]()

> 專為企業內部文件設計的翻譯與樣式校正工具，支援 PPTX/XLSX/DOCX/PDF 格式。

## 🌟 重點功能

- 🌐 **高精度多語支援**：自動偵測語言，支援繁中、英、越、日、韓。
- 🤖 **模型靈活切換**：整合 **Ollama (translategemma:4b)**、Gemini、OpenAI。
- 💾 **翻譯資料中樞 (Unified DataTable)**：全站統一使用高效能表格組件，支援動態排序、多選操作、欄位客製化配置與「載入更多」分頁機制。
- 🎨 **智慧校正介面**：視覺化標注翻譯內容，支援流暢的非受控式編輯（Uncontrolled Editing）防止鍵入衝突。
- 📦 **管理功能強化**：模組化的「管理彈窗」設計，包含對照表、術語庫、記憶庫與歷史紀錄，並支援 Compact Mode 持久化設定。

---

## 🚀 快速安裝 (Windows)

這是最推薦的安裝方式，會自動處理所有環境依賴。

### 1. 執行安裝

雙擊執行根目錄下的 **`scripts/ops/install.bat`** (將自動請求管理員限)。

### 2. 腳本動作

- 自動透過 `winget` 安裝 **Docker Desktop** 與 **Ollama**。
- 自動下載並設定 `translategemma:4b` 模型。
- 自動載入 Docker 鏡像並啟動服務。

### 3. 存取位置

- **前端介面**: [http://localhost:5195](http://localhost:5195)
- **後端 API**: [http://localhost:5005](http://localhost:5005)
- **API 文件**: [http://localhost:5005/docs](http://localhost:5005/docs)

---

## 🛠️ 維護者指南

### 📝 環境設定

複製 `.env.example` 為 `.env` 或 `backend/.env` 並根據需求調整：

- `OLLAMA_MODEL`: 預設為 `translategemma:4b`。
- `TRANSLATE_LLM_MODE`: `real` (正式翻譯) 或 `mock` (測試用)。
- `DATABASE_URL`: 本機開發的 PostgreSQL 連線字串（預設 `postgresql+psycopg://app:app@localhost:5432/appdb`）。
- `DATABASE_URL_DOCKER`: Docker 版 PostgreSQL 連線字串（預設 `postgresql+psycopg://app:app@postgres:5432/appdb`）。

### 🔎 OCR 引擎選項

- 預設使用 Tesseract。
- 若需要 PaddleOCR（更高準確率的影像字辨識），請另外安裝：
  ```powershell
  python -m pip install -r requirements-ocr-paddle.txt
  ```
- 啟用 PaddleOCR：
  - `PDF_OCR_ALLOW_PADDLE=1`
  - `PDF_OCR_ENGINE=paddle`（固定使用 PaddleOCR）
  - `PDF_OCR_PADDLE_FALLBACK=1`（Tesseract 信心不足時改用 PaddleOCR）

### 📦 安全打包與分發 (IP Protection)

如果您需要將此系統交給其他單位且**不希望暴露原始碼**：

1. 執行 `powershell -File scripts/ops/export_images.ps1`。
2. 將產出的 `release_package` 資料夾壓縮分發。
3. 接收者僅需執行其中的 `scripts/ops/install.bat` 即可運作。

### 🧹 專案清理

使用清理腳本移除快取與暫存檔：

```powershell
python scripts/cleanup/cleanup_project.py --apply
```

### 🐘 PostgreSQL 遷移

1. 啟動資料庫：
   ```powershell
   docker compose up -d postgres
   ```
2. 設定 `DATABASE_URL`：
   ```
   本機開發：postgresql+psycopg://app:app@localhost:5432/appdb
   Docker：DATABASE_URL_DOCKER=postgresql+psycopg://app:app@postgres:5432/appdb
   ```
3. 執行 Alembic：
   ```powershell
   alembic upgrade head
   ```
4. 搬移 SQLite 資料：
   ```powershell
   python scripts/migration/migrate_sqlite_to_postgres.py
   ```
5. 重新啟動後端服務

### ✅ 遷移驗證與回滾

- 驗證 SQLite 與 PostgreSQL 一致性：
  ```powershell
  python scripts/dev/verify_sqlite_postgres.py
  ```
- PostgreSQL 回滾到 SQLite：
  ```powershell
  python scripts/migration/rollback_postgres_to_sqlite.py
  ```

## 🧰 開發流程

- 安裝 `pre-commit` 並啟用：  
  ```bash
  python -m pip install pre-commit
  pre-commit install
  ```
- `pre-commit` 目前只會在 `backend/` 範圍執行 `flake8 --select=E9,F63,F7,F82`，確保重大錯誤（例如 `F821`）不會再出現。  
- 若要在開發前手動檢查所有 backend 檔案，可跑：  
  ```bash
  pre-commit run backend-only flake8 --all-files
  ```
- Layouts API contract 一鍵檢查：
  ```powershell
  python scripts/dev/run_layouts_contract_check.py
  ```
- Layouts API contract + 全測試 + 前端 build：
  ```powershell
  python scripts/dev/run_layouts_contract_check.py --full-tests --frontend-build
  ```

---

## 📂 專案結構

```
documents-translatev3/ (舊稱 PPTX-Translate)
├── scripts/ops/install.bat          # [New] Windows 一鍵安裝進入點
├── scripts/             # 自動化腳本 (安裝、打包、清理)
│   ├── cleanup/         # 清理與維護
│   ├── dev/             # 開發驗證與測試輔助
│   ├── migration/       # 資料庫遷移
│   ├── ops/             # 啟動、部署、維運
│   └── tools/           # 其他工具
├── backend/             # FastAPI 後端引擎
│   ├── api/             # 路由定義 (Naming, Translation, TM)
│   └── services/        # 核心翻譯與檔案處理邏輯
├── frontend/            # React 前端控制台
├── data/                # 運行時資料 (DB, Exports)
├── Dockerfile.backend   # 後端容器定義
├── Dockerfile.frontend  # 前端容器定義
└── README.md            # 您正在閱讀的文件
```

---

## ℹ️ 技術規格

詳細技術細節與 API 合約請參閱 [TECH_SPEC.md](TECH_SPEC.md)。

---

## 🤝 參與開發

請參考 [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) 取得開發流程、腳本分類與提交規範。

---

## 👤 作者

- **VPIC1 Japlin Chen** - *初始開發與架構設計*

---

## 🛡️ 授權與安全

- **內部使用限定**
- **資安規範**：本工具支援全區隔離運行 (Air-gapped) 當搭配 Ollama 使用時。
