# scripts 目錄說明

此目錄用於集中管理專案腳本，依用途分類如下。專業名詞維持原文。

## 目錄結構

- `cleanup/`：清理與維護  
  用途：清除快取、暫存、殘留檔案或進行專案清理。
- `dev/`：開發驗證與測試輔助  
  用途：驗證邏輯、測試資料產生、局部流程檢查。
- `migration/`：資料庫遷移  
  用途：SQLite ↔ PostgreSQL 的資料搬移與回滾。
- `ops/`：啟動、部署、維運  
  用途：安裝、啟動、Docker 相關維運、監控腳本。
- `tools/`：其他工具  
  用途：不屬於上述分類的通用工具。

## 使用原則

1. 腳本名稱要能清楚表達用途。  
2. 新增腳本時優先放入對應分類資料夾。  
3. 會產生暫存或報表的腳本，輸出請放在 `reports/` 或專用輸出資料夾。  
4. 不要把一次性或機器相關的檔案提交到 Git。

## Contract 檢查快捷方式

- 一鍵執行 Layouts API contract 檢查（含報告產生）：
  ```powershell
  python scripts/dev/run_layouts_contract_check.py
  ```
- 若要同時跑全量測試與前端 build：
  ```powershell
  python scripts/dev/run_layouts_contract_check.py --full-tests --frontend-build
  ```
- Windows 快捷入口：
  ```cmd
  scripts\ops\layouts_contract_check.cmd
  ```
