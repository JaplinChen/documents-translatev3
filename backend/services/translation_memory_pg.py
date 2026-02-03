from __future__ import annotations

from backend.services.translation_memory_pg_impl.categories import (
    create_tm_category,
    delete_tm_category,
    list_tm_categories,
    update_tm_category,
)
from backend.services.translation_memory_pg_impl.db import _ensure_db
from backend.services.translation_memory_pg_impl.feedback import get_learned_terms, record_term_feedback
from backend.services.translation_memory_pg_impl.flags import is_postgres_enabled
from backend.services.translation_memory_pg_impl.glossary import (
    apply_glossary,
    batch_delete_glossary,
    batch_upsert_glossary,
    clear_glossary,
    delete_glossary,
    get_glossary,
    get_glossary_count,
    get_glossary_terms,
    get_glossary_terms_any,
    seed_glossary,
    upsert_glossary,
)
from backend.services.translation_memory_pg_impl.learning import (
    _record_learning_event,
    list_learning_events,
    list_learning_stats,
)
from backend.services.translation_memory_pg_impl.tm import (
    batch_delete_tm,
    clear_tm,
    delete_tm,
    get_tm,
    get_tm_count,
    get_tm_terms,
    get_tm_terms_any,
    lookup_tm,
    save_tm,
    seed_tm,
    upsert_tm,
)
from backend.services.translation_memory_pg_impl.utils import _hash_text

__all__ = [
    "_ensure_db",
    "_hash_text",
    "_record_learning_event",
    "apply_glossary",
    "batch_delete_glossary",
    "batch_delete_tm",
    "batch_upsert_glossary",
    "clear_glossary",
    "clear_tm",
    "create_tm_category",
    "delete_glossary",
    "delete_tm",
    "delete_tm_category",
    "get_glossary",
    "get_glossary_count",
    "get_glossary_terms",
    "get_glossary_terms_any",
    "get_learned_terms",
    "get_tm",
    "get_tm_count",
    "get_tm_terms",
    "get_tm_terms_any",
    "is_postgres_enabled",
    "list_learning_events",
    "list_learning_stats",
    "list_tm_categories",
    "lookup_tm",
    "record_term_feedback",
    "save_tm",
    "seed_glossary",
    "seed_tm",
    "update_tm_category",
    "upsert_glossary",
    "upsert_tm",
]
