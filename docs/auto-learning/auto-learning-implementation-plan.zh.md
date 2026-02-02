# 自動學習實施計畫（Draft v1）

## Phase 0：準備（1 週）
- 確認規模（使用者數、TM 增長速率、SLA）
- 固定評分/升級/衰減門檻
- 選定 Worker 模式（獨立容器或內建排程）

## Phase 1：PostgreSQL 遷移（2 週）
- docker-compose 增加 postgres 服務
- 導入 DATABASE_URL 設定
- 建立資料存取層（SQLAlchemy 或 asyncpg）
- SQLite -> PostgreSQL 資料搬移
- 驗證資料一致性

## Phase 2：資料模型擴充（1 週）
- 新增 learning_candidates、learning_events、learning_stats
- 新增欄位 last_used_at、overwrite_count、source_type、scope_id
- 索引優化

## Phase 3：學習 Worker（2 週）
- 建置排程或常駐 Worker
- 批次匯入/清洗流程
- 評分與升級邏輯
- 衰減與淘汰機制

## Phase 4：執行期整合（1 週）
- 翻譯流程新增 learning event 紀錄
- 抽取術語使用 learned_context
- TM/Glossary 查詢加上 scope 與衰減條件

## Phase 5：監控與指標（1 週）
- 寫入 learning_stats
- 追蹤 TM 命中率、Glossary 命中率、覆寫率
- 匯出簡易報表或 API

## Phase 6：上線（1 週）
- 先在 staging 啟用
- 分批導入 production
- 依 KPI 調整門檻

## 風險與對策
- 資料損壞：分段遷移 + 回滾方案
- 效能壓力：索引 + 批次處理
- 過度學習：門檻調整 + 衰減

## 測試策略
- 評分、清洗、升級 unit tests
- 端到端整合測試
- PostgreSQL 併發壓力測試

## 回滾方案
- 保留 SQLite 快照（唯讀）
- 關閉 Worker 回到事件驅動

