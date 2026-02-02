# Auto-Learning System Spec (Draft v1)

## 1. Purpose
Provide a fully automated learning pipeline that improves terminology extraction, translation consistency, and classification quality without human review. The system must be safe, self-correcting, and scalable for multi-user usage.

## 2. Scope
- In scope:
  - Automated learning from bilingual content and user feedback
  - Term extraction improvement (prompt context + data quality)
  - Translation Memory (TM) quality improvement
  - Automatic domain/category classification
  - PostgreSQL migration and Docker-based deployment
- Out of scope:
  - Model fine-tuning or external ML training pipelines
  - Human review workflows

## 3. Current State Summary (Baseline)
- Learning is event-driven only (no background worker).
- Term feedback is stored in `term_feedback` and auto-promoted to `glossary` at a fixed threshold.
- TM is written on translation completion and used via exact match.
- Domain detection is keyword-based.
- Storage is SQLite (`translation_memory.db`, `terms.db`).

## 4. Goals and Non-Goals
### Goals
- Fully automated learning without human intervention.
- Improve correctness by reducing noisy/incorrect entries.
- Scale for multi-user, multi-project usage.
- Provide automated rollbacks via decay and overwrite signals.

### Non-Goals
- No training or fine-tuning of language models.
- No manual approval steps.

## 5. High-Level Architecture
- Services:
  - API (backend)
  - Worker (scheduled or continuous)
  - PostgreSQL database
- Storage:
  - `translation_memory` tables (tm, glossary, term_feedback)
  - `terms` (unified terminology)
  - `learning_events`, `learning_stats`

## 6. Auto-Learning Pipeline (8 Stages)
1) Ingestion
- Inputs: bilingual files, translation outputs, user corrections
- Normalize and segment into aligned source/target pairs

2) Cleaning and De-noise
- Drop empty, numeric-only, language-mismatch pairs
- Filter low-quality TM entries
- Deduplicate by (source, target, lang)

3) Term Mining
- Rule-based extraction (acronyms, brands, technical terms)
- LLM-assisted extraction from sampled content

4) Auto Classification
- Assign domain/category using rules + embedding/LLM classification
- Store `domain_score` and `category_score`

5) Auto Promotion
- Weighted confidence score for each candidate
- Promote to:
  - Staging pool
  - TM
  - Glossary (only if score passes high threshold)

6) Auto Decay and Eviction
- Decay by time or non-usage
- Evict entries with high overwrite rate

7) Feedback Loop
- Use learned terms as prompt context
- Use TM/glossary to guide translation

8) Monitoring and Auto-Tuning
- Track hit-rate, overwrite-rate, and translation consistency
- Auto-adjust thresholds

## 7. Scoring and Promotion Rules
- Candidate score = frequency * context_similarity * alignment_quality * recency
- Example thresholds:
  - score >= 0.85 -> glossary
  - score >= 0.65 -> TM
  - score >= 0.45 -> staging

## 8. Data Model (Proposed)
### Core Tables
- tm
- glossary
- term_feedback
- terms

### New Tables
- learning_candidates
- learning_events
- learning_stats

### Key Fields (examples)
- `source_text`, `target_text`, `source_lang`, `target_lang`
- `domain`, `category`, `confidence`, `last_used_at`, `overwrite_count`
- `source_type` (auto|feedback|import)
- `scope_id` (project/user)

## 9. Data Lifecycle
- New entries are staged before promotion.
- Stale or frequently overwritten entries decay and are removed.
- All learning operations are append-only events in `learning_events` for traceability.

## 10. Operational Requirements
- Must support concurrent users.
- DB must scale to 1M+ TM entries.
- Automated backups for PostgreSQL.

## 11. Success Metrics (KPIs)
- TM hit rate
- Glossary hit rate
- Overwrite rate
- Term extraction precision/recall (sampled)

## 12. Risks and Mitigations
- Risk: Wrong auto-learning from noisy input
  - Mitigation: weighted scoring + decay + overwrite detection
- Risk: DB growth
  - Mitigation: decay/eviction and archiving

