from __future__ import annotations

from .db import _connect, _ensure_db


def _check_term_duplicate(term_norm: str, exclude_id: int | None = None) -> None:
    _ensure_db()
    query = "SELECT id FROM terms WHERE term_norm = ?"
    params: list[object] = [term_norm]
    if exclude_id:
        query += " AND id != ?"
        params.append(exclude_id)
    with _connect() as conn:
        row = conn.execute(query, params).fetchone()
    if row:
        raise ValueError("術語已存在")


def _check_alias_conflict(alias_norms: list[str], exclude_term_id: int | None = None) -> None:
    _ensure_db()
    if not alias_norms:
        return
    placeholders = ",".join(["?"] * len(alias_norms))
    query = f"SELECT term_id FROM term_aliases WHERE alias_norm IN ({placeholders})"
    params: list[object] = [*alias_norms]
    if exclude_term_id:
        query += " AND term_id != ?"
        params.append(exclude_term_id)
    with _connect() as conn:
        row = conn.execute(query, params).fetchone()
    if row:
        raise ValueError("別名與現有術語衝突")
