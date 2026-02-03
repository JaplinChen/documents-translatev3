from __future__ import annotations

from backend.config import settings


def is_postgres_enabled() -> bool:
    url = settings.database_url or ""
    return url.startswith("postgresql")
