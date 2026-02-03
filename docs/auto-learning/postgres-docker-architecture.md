# PostgreSQL + Docker 架構說明（草案 v2）

## 拓撲
- frontend -> backend -> postgres
- 全部服務同一 docker network

## 服務
- postgres
  - Image: postgres:15（或公司標準）
  - Persistent volume: pg_data
  - Healthcheck 啟用
  - 建議預設 `max_connections` 與 `shared_buffers` 配置
- backend
  - 使用 DATABASE_URL 連線
- frontend
  - 不直接連 DB

## 環境變數
- `DATABASE_URL=postgresql://app:app@postgres:5432/appdb`
- 本機開發可改成 `localhost:5432`

## Volumes
- `pg_data:/var/lib/postgresql/data`
- `backups:/backups`（選用）

## 備份策略
- 每日 `pg_dump`
- 保留 7-30 天
- 備份目錄與容器分離存放

## 佈署注意事項
- production 建議獨立 DB 伺服器或受管服務
- 測試與 staging 使用獨立資料庫

## 遷移注意事項
- 一次性 SQLite -> PostgreSQL 匯入
- 驗證筆數與 checksum
- 遷移策略：snapshot -> bulk import -> delta sync -> cutover
- 切換後保留回滾窗口
