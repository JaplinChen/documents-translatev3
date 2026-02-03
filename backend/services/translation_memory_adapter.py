from __future__ import annotations

from backend.config import settings


def _use_postgres() -> bool:
    url = settings.database_url or ""
    return url.startswith("postgresql")


if _use_postgres():
    from backend.services.translation_memory_pg import *  # noqa: F401,F403
else:
    from backend.services.translation_memory import *  # noqa: F401,F403

