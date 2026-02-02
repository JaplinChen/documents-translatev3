# PostgreSQL + Docker 架構說明（Draft v1）

## 拓撲
- frontend -> backend -> postgres
- 全部服務同一 docker network

## 服務
- postgres
  - Image: postgres:15（或公司標準）
  - Persistent volume: pg_data
  - Healthcheck 啟用
- backend
  - 使用 DATABASE_URL 連線
- frontend
  - 不直接連 DB

## 環境變數
- DATABASE_URL=postgresql://user:pass@postgres:5432/appdb

## Volumes
- pg_data:/var/lib/postgresql/data
- backups:/backups（選用）

## 備份策略
- 每日 pg_dump
- 保留 7-30 天

## 遷移注意事項
- 一次性 SQLite -> PostgreSQL 匯入
- 驗證筆數與 checksum

