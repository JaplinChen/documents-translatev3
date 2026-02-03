from __future__ import annotations

from backend.services.translation_memory_sqlite.categories import (
    create_tm_category,
    delete_tm_category,
    list_tm_categories,
    update_tm_category,
)
from backend.services.translation_memory_sqlite import db as sqlite_db
from backend.services.translation_memory_sqlite.db import DB_PATH, SCHEMA_SQL, _ensure_db
from backend.services.translation_memory_sqlite.glossary import (
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
from backend.services.translation_memory_sqlite.learning import (
    _record_learning_event,
    list_learning_events,
    list_learning_stats,
)
from backend.services.translation_memory_sqlite import tm as sqlite_tm
from backend.services.translation_memory_sqlite import tm_admin, tm_ingest, tm_query
from backend.services.translation_memory_sqlite.tm import (
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
from backend.services.translation_memory_sqlite.utils import _hash_text

_DB_INITIALIZED = sqlite_db._DB_INITIALIZED


def _sync_db_state() -> None:
    sqlite_db.DB_PATH = DB_PATH
    sqlite_db._DB_INITIALIZED = _DB_INITIALIZED
    tm_admin.DB_PATH = DB_PATH
    tm_ingest.DB_PATH = DB_PATH
    tm_query.DB_PATH = DB_PATH


def _refresh_db_state() -> None:
    global DB_PATH, _DB_INITIALIZED
    DB_PATH = sqlite_db.DB_PATH
    _DB_INITIALIZED = sqlite_db._DB_INITIALIZED


def seed_tm(items):
    _sync_db_state()
    result = sqlite_tm.seed_tm(items)
    _refresh_db_state()
    return result


def get_tm(*args, **kwargs):
    _sync_db_state()
    result = sqlite_tm.get_tm(*args, **kwargs)
    _refresh_db_state()
    return result


def clear_tm(*args, **kwargs):
    _sync_db_state()
    result = sqlite_tm.clear_tm(*args, **kwargs)
    _refresh_db_state()
    return result

__all__ = [
    "DB_PATH",
    "SCHEMA_SQL",
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
    "get_tm",
    "get_tm_count",
    "get_tm_terms",
    "get_tm_terms_any",
    "list_learning_events",
    "list_learning_stats",
    "list_tm_categories",
    "lookup_tm",
    "save_tm",
    "seed_glossary",
    "seed_tm",
    "update_tm_category",
    "upsert_glossary",
    "upsert_tm",
]
