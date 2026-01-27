# 企業常用文件翻譯與校正控制台 (Documents-Translate)

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-內部使用-lightgrey.svg)]()

> 專為企業內部文件設計的翻譯與樣式校正工具，支援 PPTX/XLSX/DOCX/PDF 格式。

## 🌟 重點功能

- 🌐 **高精度多語支援**：自動偵測語言，支援繁中、英、越、日、韓。
- 🤖 **模型靈活切換**：整合 **Ollama (translategemma:4b)**、Gemini、OpenAI。
- 💾 **翻譯記憶與術語**：內建 SQLite 儲存空間，支援高密度懸浮佈局 (Sticky Header) 管理。
- 🎨 **智慧校正介面**：視覺化標注翻譯內容，支援流暢的非受控式編輯（Uncontrolled Editing）防止鍵入衝突。
- 📦 **安全發布機制**：支援「鏡像打包」模式，可保護原始碼進行跨電腦分發。

---

## 🚀 快速安裝 (Windows)

這是最推薦的安裝方式，會自動處理所有環境依賴。

### 1. 執行安裝

雙擊執行根目錄下的 **`install.bat`** (將自動請求管理員限)。

### 2. 腳本動作

- 自動透過 `winget` 安裝 **Docker Desktop** 與 **Ollama**。
- 自動下載並設定 `translategemma:4b` 模型。
- 自動載入 Docker 鏡像並啟動服務。

### 3. 存取位置

- **前端介面**: [http://localhost:5194](http://localhost:5194)
- **後端 API**: [http://localhost:5002](http://localhost:5002)
- **API 文件**: [http://localhost:5002/docs](http://localhost:5002/docs)

---

## 🛠️ 維護者指南

### 📝 環境設定

複製 `.env.example` 為 `.env` 或 `backend/.env` 並根據需求調整：

- `OLLAMA_MODEL`: 預設為 `translategemma:4b`。
- `TRANSLATE_LLM_MODE`: `real` (正式翻譯) 或 `mock` (測試用)。

### 📦 安全打包與分發 (IP Protection)

如果您需要將此系統交給其他單位且**不希望暴露原始碼**：

1. 執行 `powershell -File scripts/export_images.ps1`。
2. 將產出的 `release_package` 資料夾壓縮分發。
3. 接收者僅需執行其中的 `install.bat` 即可運作。

### 🧹 專案清理

使用清理腳本移除快取與暫存檔：

```powershell
python scripts/cleanup_project.py --no-dry-run
```

---

## 📂 專案結構

```
PPTX-Translate/
├── install.bat          # [New] Windows 一鍵安裝進入點
├── scripts/             # 自動化腳本 (安裝、打包、清理)
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

## 👤 作者

- **VPIC1 Japlin Chen** - *初始開發與架構設計*

---

## 🛡️ 授權與安全

- **內部使用限定**
- **資安規範**：本工具支援全區隔離運行 (Air-gapped) 當搭配 Ollama 使用時。
