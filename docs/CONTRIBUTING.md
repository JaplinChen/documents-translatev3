# 參與開發說明

此文件說明專案的基本開發規範與流程，所有內容以繁體中文為準，專業名詞維持原文。

## 開發環境

1. 安裝 Python（建議 3.10+）。  
2. 安裝 Node.js（供前端使用）。  
3. 若使用 Docker，請安裝 Docker Desktop。  

## 專案啟動

- Windows 一鍵安裝  
  執行：`scripts/ops/install.bat`

- Docker 啟動  
  執行：`scripts/ops/start_docker.bat` 或 `scripts/ops/start_docker.sh`

## 目錄與腳本規範

- 主要腳本集中於 `scripts/` 目錄並依用途分類。  
  詳細結構請參考 `scripts/README.md`。

## 清理與報表

- 清理腳本  
  執行：`python scripts/cleanup/cleanup_project.py --apply`

- 報表與暫存  
  請放在 `reports/`，避免提交到 Git。

## 提交規範

1. 提交前請確認不包含以下類型的檔案：  
   - 快取、暫存、備份檔案  
   - 產出報表與一次性資料  
   - 本機環境設定檔
2. 若涉及大範圍變更，建議先拆分成多個小提交。  
3. 新增功能請附上必要測試，或在說明中註明測試範圍。

## 測試

- 執行測試：`pytest -q`

## 其他

如需新增新的工具或腳本，請先確認是否已有相近功能，並保持分類一致。
