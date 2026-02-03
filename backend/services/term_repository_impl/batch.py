from __future__ import annotations

from .db import _connect, _ensure_db


def batch_update_terms(
    term_ids: list[int],
    category_id: int | None = None,
    status: str | None = None,
    case_rule: str | None = None,
    source: str | None = None,
    priority: int | None = None,
) -> int:
    _ensure_db()
    if not term_ids:
        return 0
    updates = []
    params: list = []
    if category_id is not None:
        updates.append("category_id = ?")
        params.append(category_id)
    if status is not None:
        updates.append("status = ?")
        params.append(status)
    if case_rule is not None:
        updates.append("case_rule = ?")
        params.append(case_rule)
    if source is not None:
        updates.append("source = ?")
        params.append(source)
    if priority is not None:
        updates.append("priority = ?")
        params.append(priority)
    if not updates:
        return 0
    params.append(tuple(term_ids))
    sql = (
        "UPDATE terms SET "
        + ", ".join(updates)
        + ", updated_at = CURRENT_TIMESTAMP "
        + f"WHERE id IN ({','.join(['?'] * len(term_ids))})"
    )
    with _connect() as conn:
        cur = conn.execute(sql, params[:-1] + term_ids)
        return cur.rowcount


def batch_delete_terms(term_ids: list[int]) -> int:
    _ensure_db()
    if not term_ids:
        return 0
    placeholders = ",".join(["?"] * len(term_ids))
    with _connect() as conn:
        conn.execute(
            f"DELETE FROM term_languages WHERE term_id IN ({placeholders})",
            term_ids,
        )
        conn.execute(
            f"DELETE FROM term_aliases WHERE term_id IN ({placeholders})",
            term_ids,
        )
        cur = conn.execute(
            f"DELETE FROM terms WHERE id IN ({placeholders})",
            term_ids,
        )
        return cur.rowcount
