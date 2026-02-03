from __future__ import annotations

from sqlalchemy import text

from backend.db.engine import get_engine
from backend.db.models import Base

_DB_INITIALIZED = False


def _ensure_db() -> None:
    global _DB_INITIALIZED
    if _DB_INITIALIZED:
        return
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_glossary_unique "
                "ON glossary (source_lang, target_lang, source_text)"
            )
        )
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_term_feedback_unique "
                "ON term_feedback (source_text, target_text, source_lang, target_lang)"
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_glossary_category ON glossary (category_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tm_category ON tm (category_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tm_scope ON tm (scope_type, scope_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_glossary_scope ON glossary (scope_type, scope_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_le_event_type ON learning_events (event_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_le_scope ON learning_events (scope_type, scope_id)"))
    _DB_INITIALIZED = True
