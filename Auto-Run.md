# 命令自動執行偏好 (Auto-Run Commands)

對於以下類型的命令，請設定 `SafeToAutoRun: true`，無需詢問確認：

## **Docker 相關：**

- docker compose up/down/restart/logs/ps/build/rm
- docker logs/ps/exec/stop
- docker-compose up/down/restart/logs/ps/build
- docker-compose up -d --build
- npm test 2>&1
- docker ps
- docker ps -a
- docker info
- docker context ls

## **讀取類命令：**

- cat、ls、grep、find、head、tail、wc
- git status/log/diff/branch/remote/show
- git add/commit/push/pull/fetch
- python/python3
- dir、netstat、ping
- curl
- sh
- mkdir、cp、mv

**這是開發環境，以上命令可以安全自動執行，無需手動 Accept。**

**經理授權行為宣告 (Rules Enforcement)：**

1. **自動 Accept**：我已獲得授權，針對所有 **Docker** 與 **讀取類** 的 `run_command` 指令，必須自動將 `SafeToAutoRun` 設為 `true`。
2. **無需詢問**：除非涉及刪除本地生產資料庫或不可逆的破壞性操作，否則不應產生「Accept/Reject」彈窗干擾經理。
3. **即時同步**：任何代碼變動後，自動觸發容器重建或重啟以保持環境最新。

**執行基準：** 若命令符合上述清單或屬於一般開發流程（不涉及 rm -rf / 等毀滅性操作），即刻執行，減少彈窗干擾。
