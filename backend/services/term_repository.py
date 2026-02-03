from __future__ import annotations

from backend.services.term_repository_impl.batch import batch_delete_terms, batch_update_terms
from backend.services.term_repository_impl.categories import (
    create_category,
    delete_category,
    get_category_id_by_name,
    list_categories,
    update_category,
)
from backend.services.term_repository_impl.db import DB_PATH, SCHEMA_SQL, _connect, _ensure_db
from backend.services.term_repository_impl.sync import (
    delete_by_term,
    sync_from_external,
    upsert_term_by_norm,
)
from backend.services.term_repository_impl.terms_read import (
    get_term,
    list_terms,
    list_versions,
)
from backend.services.term_repository_impl.terms_write import (
    create_term,
    delete_term,
    update_term,
)

__all__ = [
    "DB_PATH",
    "SCHEMA_SQL",
    "_connect",
    "_ensure_db",
    "batch_delete_terms",
    "batch_update_terms",
    "create_category",
    "create_term",
    "delete_by_term",
    "delete_category",
    "delete_term",
    "get_category_id_by_name",
    "get_term",
    "list_categories",
    "list_terms",
    "list_versions",
    "sync_from_external",
    "update_category",
    "update_term",
    "upsert_term_by_norm",
]
