# Auto-Learning Implementation Plan (Draft v1)

## Phase 0: Preparation (1 week)
- Confirm target scale (users, TM growth rate, SLA)
- Finalize thresholds for scoring/promotion/decay
- Decide worker mode: separate container vs backend scheduler

## Phase 1: PostgreSQL Migration (2 weeks)
- Add postgres service to docker-compose
- Introduce DATABASE_URL and config wiring
- Implement data access layer (SQLAlchemy or asyncpg)
- Build migration scripts from SQLite to PostgreSQL
- Smoke tests and data validation

## Phase 2: Data Model Extensions (1 week)
- Add tables: learning_candidates, learning_events, learning_stats
- Add fields: last_used_at, overwrite_count, source_type, scope_id
- Add indexes for fast lookup

## Phase 3: Learning Worker (2 weeks)
- Implement scheduler or worker container
- Batch ingestion + cleaning pipeline
- Scoring and promotion rules
- Decay and eviction routines

## Phase 4: Runtime Integration (1 week)
- Update translation pipeline to record learning events
- Update term extraction to use learned context
- Update TM/glossary lookup with scope and decay flags

## Phase 5: Monitoring & Metrics (1 week)
- Add metrics collection to learning_stats
- Track TM hit rate, glossary hit rate, overwrite rate
- Add simple report endpoint or periodic CSV export

## Phase 6: Rollout (1 week)
- Enable in staging with limited scope
- Gradually enable in production
- Monitor KPIs and adjust thresholds

## Risks and Mitigation
- Data corruption: use staged migration + rollback plan
- Performance: add indexes and batch jobs
- Over-learning: tune thresholds + decay

## Testing Strategy
- Unit tests for scoring, cleaning, promotion
- Integration tests for end-to-end pipeline
- Load test for PostgreSQL under concurrent access

## Rollback Plan
- Keep SQLite read-only snapshot
- Disable worker and revert to event-driven path

