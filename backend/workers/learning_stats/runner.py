from __future__ import annotations

from datetime import date, timedelta

from backend.config import settings

from .postgres import compute_daily_stats_pg
from .sqlite import compute_daily_stats_sqlite


def compute_daily_stats(
    stat_date: date, scope_type: str = "project", scope_id: str | None = "default"
):
    if (settings.database_url or "").startswith("postgresql"):
        return compute_daily_stats_pg(stat_date, scope_type=scope_type, scope_id=scope_id)
    return compute_daily_stats_sqlite(stat_date, scope_type=scope_type, scope_id=scope_id)


def run_daily_stats(
    scope_type: str = "project", scope_id: str | None = "default", days_back: int = 1
):
    target_date = date.today() - timedelta(days=days_back)
    return compute_daily_stats(target_date, scope_type=scope_type, scope_id=scope_id)
