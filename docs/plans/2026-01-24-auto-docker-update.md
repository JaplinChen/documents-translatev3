# Auto Docker Update Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 登入後自動偵測 git 更新並執行 `docker compose build` + `docker compose up -d`。

**Architecture:** 以常駐 PowerShell 腳本輪詢 `origin/main` commit；若變更則 `git pull` 後重建並重啟。搭配 Windows 啟動捷徑於登入後自動執行。

**Tech Stack:** PowerShell、Git、Docker Compose、Windows Startup

### Task 1: 新增常駐更新腳本

**Files:**
- Create: `watch_update.ps1`

**Step 1: Write the failing test**
（此類腳本以功能驗證為主，跳過單元測試；使用手動執行驗證。）

**Step 2: Run test to verify it fails**
Run: `powershell -NoProfile -ExecutionPolicy Bypass -File watch_update.ps1 -RepoPath .`
Expected: 無 log 檔案、未觸發更新。

**Step 3: Write minimal implementation**
- 每 N 秒 `git fetch origin main`
- 比對 `origin/main` 與 `HEAD`
- 變更時執行 `git pull`、`docker compose build`、`docker compose up -d`
- 記錄 log
- dirty worktree 時跳過
- lock 檔避免重入

**Step 4: Run test to verify it passes**
Expected: `logs/watch_update.log` 產生，並在有更新時執行 build/up。

**Step 5: Commit**
```bash
git add watch_update.ps1
git commit -m "feat: add auto update watcher"
```

### Task 2: 建立啟動入口

**Files:**
- Create: `watch_update.cmd`

**Step 1: Write the failing test**
手動雙擊執行，確認不會被 PowerShell 執行政策阻擋。

**Step 2: Run test to verify it fails**
Expected: 無法啟動或未能執行 `watch_update.ps1`。

**Step 3: Write minimal implementation**
- `powershell -NoProfile -ExecutionPolicy Bypass -File watch_update.ps1 -RepoPath "%REPO%"`

**Step 4: Run test to verify it passes**
Expected: `watch_update.ps1` 正常啟動並寫入 log。

**Step 5: Commit**
```bash
git add watch_update.cmd
git commit -m "feat: add watcher launcher"
```

### Task 3: 設定登入後自動啟動

**Files:**
- Create: Windows Startup 捷徑指向 `watch_update.cmd`

**Step 1: Write the failing test**
登出/登入後檢查是否有 `watch_update.log`。

**Step 2: Run test to verify it fails**
Expected: 未自動啟動、無 log。

**Step 3: Write minimal implementation**
- 建立捷徑於 `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\`

**Step 4: Run test to verify it passes**
Expected: 登入後自動啟動並產生 log。

**Step 5: Commit**
（系統捷徑不納入 git）
