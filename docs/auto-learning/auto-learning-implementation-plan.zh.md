# 自動學習實施計畫（草案 v2）

## 已落地（SQLite 版）
- TM/Glossary 增加 scope_type/scope_id/domain/category/status/hit_count/last_hit_at/overwrite_count 欄位
- TM 查詢新增 fuzzy/partial match（含 domain/category bonus）
- 新增 learning_events、learning_stats 表（SQLite）
- 翻譯流程寫入 learning_events（lookup_hit/lookup_miss/overwrite 等）
- 每日統計 Worker 寫入 learning_stats
- Worker 以 FastAPI lifespan 啟動並在 shutdown 時取消

## 0. 前置決策（本計畫固定）
- ORM：SQLAlchemy 2.0
- Migration：Alembic
- Schema：snake_case、bigint 主鍵、timestamptz、jsonb 事件欄位
- Worker：`backend/workers/` 內建排程（先內建，保留獨立容器選項）

## Phase 0：準備（1 週）
### 工作項目
- 確認規模（使用者數、TM 增長速率、SLA）
- 固定評分/升級/衰減門檻
- 定義 scope 層級（user/project/org/global）與查詢優先序
- 定義事件 schema 與可觀測性指標
- 設計資料生命週期與衰減策略

### 產出物
- 規格書 v2
- KPI/告警門檻清單
- 事件欄位與查詢欄位清單

## Phase 1：PostgreSQL 遷移（2 週）
### 工作項目
- docker-compose 增加 postgres 服務
- 導入 DATABASE_URL 設定
- 建立資料存取層（SQLAlchemy）
- SQLite -> PostgreSQL 資料搬移
- 驗證資料一致性
- 遷移策略：snapshot -> bulk import -> delta sync -> cutover
- 建立 checksum 與 row count 比對腳本

### 產出物
- PostgreSQL schema + migration
- 遷移腳本與驗證報告
- 回滾腳本

## Phase 2：資料模型擴充（1 週）
### 工作項目
- 新增 learning_candidates、learning_events、learning_stats
- 新增欄位 last_used_at、overwrite_count、source_type、scope_id
- 索引優化
- 新增狀態欄位（status、hit_count、last_hit_at）
- 定義事件表欄位（event_type、before_payload、after_payload）

### 產出物
- SQLAlchemy models
- Alembic migrations
- DDL 文件

## Phase 3：學習 Worker（2 週）
### 工作項目
- 建置排程或常駐 Worker
- 批次匯入/清洗流程
- 評分與升級邏輯
- 衰減與淘汰機制
- idempotency key 防止重複升級
- 影子模式（只計算，不升級）

### 產出物
- `backend/workers/` 模組
- 排程與作業記錄
- 指標與告警紀錄

## Phase 4：執行期整合（1 週）
### 工作項目
- 翻譯流程新增 learning event 紀錄
- 抽取術語使用 learned_context
- TM/Glossary 查詢加上 scope 與衰減條件
- TM 查詢新增 fuzzy/partial match（含最小信心閾值）
- 建立 fuzzy/partial match 基準測試與 A/B 設定

### 產出物
- API 事件紀錄
- TM/Glossary 查詢行為更新
- 測試報告

## Phase 5：監控與指標（1 週）
### 工作項目
- 寫入 learning_stats
- 追蹤 TM 命中率、Glossary 命中率、覆寫率
- 匯出簡易報表或 API
- 追蹤自動升級錯誤率、錯誤建議率
- 設定警報門檻與自動降級策略
- 建立 KPI 門檻預設值與調參流程

### 產出物
- KPI 報表
- 告警設定
- 調參流程文件

## Phase 6：上線（1 週）
### 工作項目
- 先在 staging 啟用
- 分批導入 production
- 依 KPI 調整門檻

### 產出物
- 上線紀錄
- KPI 觀測報告

## PostgreSQL 遷移落地步驟（已提供腳本）
1. 啟動服務：`docker compose up -d postgres`
2. 設定資料庫連線（本機與 Docker 分開）
   - 本機開發：`DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/appdb`
   - Docker：`DATABASE_URL_DOCKER=postgresql+psycopg://app:app@postgres:5432/appdb`
3. 執行 migration：`alembic upgrade head`
4. 資料搬移：`python scripts/migrate_sqlite_to_postgres.py`
5. 重新啟動後端服務
6. 驗證一致性：`python scripts/verify_sqlite_postgres.py`
7. 回滾（必要時）：`python scripts/rollback_postgres_to_sqlite.py`

## 測試策略
- 評分、清洗、升級 unit tests
- 端到端整合測試
- PostgreSQL 併發壓力測試
- 遷移一致性測試（checksum/row count）

## 回滾方案
- 保留 SQLite 快照（唯讀）
- 關閉 Worker 回到事件驅動
- 切回資料庫連線並停用新特性
