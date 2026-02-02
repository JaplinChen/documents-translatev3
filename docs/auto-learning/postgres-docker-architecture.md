# PostgreSQL-in-Docker Architecture (Draft v1)

## Topology
- frontend -> backend -> postgres
- All services in same Docker network

## Services
- postgres
  - Image: postgres:15 (or org standard)
  - Persistent volume: pg_data
  - Healthcheck enabled
- backend
  - Connect via DATABASE_URL
- frontend
  - No direct DB access

## Environment Variables
- DATABASE_URL=postgresql://user:pass@postgres:5432/appdb

## Volumes
- pg_data:/var/lib/postgresql/data
- backups:/backups (optional)

## Backup Strategy
- Daily pg_dump to /backups
- Retention: 7-30 days

## Migration Notes
- One-time import from SQLite to PostgreSQL
- Validate row counts and checksum

