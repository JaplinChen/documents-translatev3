from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB_PATH = Path("data/terms.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS categories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  sort_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS terms (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  term TEXT NOT NULL,
  term_norm TEXT NOT NULL,
  category_id INTEGER,
  status TEXT NOT NULL,
  case_rule TEXT,
  note TEXT,
  source TEXT,
  created_by TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS term_languages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  term_id INTEGER NOT NULL,
  lang_code TEXT NOT NULL,
  value TEXT,
  value_norm TEXT,
  UNIQUE(term_id, lang_code)
);

CREATE TABLE IF NOT EXISTS term_aliases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  term_id INTEGER NOT NULL,
  alias TEXT NOT NULL,
  alias_norm TEXT NOT NULL,
  UNIQUE(term_id, alias_norm)
);

CREATE TABLE IF NOT EXISTS term_versions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  term_id INTEGER NOT NULL,
  diff TEXT,
  created_by TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

_DB_INITIALIZED = False


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_db() -> None:
    global _DB_INITIALIZED
    if _DB_INITIALIZED and DB_PATH.exists():
        return
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.executescript(SCHEMA_SQL)
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_terms_norm ON terms (term_norm)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_term_lang_code ON term_languages (lang_code)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_term_alias_norm ON term_aliases (alias_norm)")
        # Check if source column exists
        cursor = conn.execute("PRAGMA table_info(terms)")
        columns = [row["name"] for row in cursor.fetchall()]
        if "source" not in columns:
            conn.execute("ALTER TABLE terms ADD COLUMN source TEXT")
    _DB_INITIALIZED = True


def _normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return " ".join(text.strip().split())


def list_categories() -> list[dict]:
    _ensure_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, name, sort_order FROM categories ORDER BY sort_order, id"
        ).fetchall()
    return [dict(row) for row in rows]


def get_category_id_by_name(name: str) -> int | None:
    _ensure_db()
    normalized = _normalize_text(name)
    if not normalized:
        return None
    with _connect() as conn:
        row = conn.execute(
            "SELECT id FROM categories WHERE name = ?",
            (normalized,),
        ).fetchone()
    return int(row["id"]) if row else None


def create_category(name: str, sort_order: int | None = None) -> dict:
    _ensure_db()
    if not name or not name.strip():
        raise ValueError("分類不可為空")
    normalized = _normalize_text(name)
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO categories (name, sort_order) VALUES (?, ?)",
            (normalized, sort_order or 0),
        )
        return {
            "id": cur.lastrowid,
            "name": normalized,
            "sort_order": sort_order or 0,
        }


def update_category(category_id: int, name: str, sort_order: int | None = None) -> dict:
    _ensure_db()
    normalized = _normalize_text(name)
    with _connect() as conn:
        conn.execute(
            "UPDATE categories SET name = ?, sort_order = ? WHERE id = ?",
            (normalized, sort_order or 0, category_id),
        )
        row = conn.execute(
            "SELECT id, name, sort_order FROM categories WHERE id = ?",
            (category_id,),
        ).fetchone()
    if not row:
        raise ValueError("分類不存在")
    return dict(row)


def delete_category(category_id: int) -> None:
    _ensure_db()
    with _connect() as conn:
        conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))


def _get_or_create_category(
    category_id: int | None,
    category_name: str | None,
    allow_create: bool = True,
) -> int | None:
    if category_id:
        return category_id
    if not category_name:
        return None
    normalized = _normalize_text(category_name)
    with _connect() as conn:
        row = conn.execute(
            "SELECT id FROM categories WHERE name = ?",
            (normalized,),
        ).fetchone()
        if row:
            return int(row["id"])
        if not allow_create:
            raise ValueError("分類不存在")
        cur = conn.execute(
            "INSERT INTO categories (name, sort_order) VALUES (?, 0)",
            (normalized,),
        )
        return cur.lastrowid


def _check_term_duplicate(term_norm: str, exclude_id: int | None = None) -> None:
    with _connect() as conn:
        if exclude_id:
            row = conn.execute(
                "SELECT id FROM terms WHERE term_norm = ? AND id != ?",
                (term_norm, exclude_id),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT id FROM terms WHERE term_norm = ?",
                (term_norm,),
            ).fetchone()
    if row:
        raise ValueError("術語已存在")


def _check_alias_conflict(alias_norms: list[str], exclude_term_id: int | None = None) -> None:
    if not alias_norms:
        return
    with _connect() as conn:
        for alias_norm in alias_norms:
            row = conn.execute(
                "SELECT id FROM terms WHERE term_norm = ?",
                (alias_norm,),
            ).fetchone()
            if row:
                raise ValueError("別名與現有術語衝突")
            if exclude_term_id:
                conflict = conn.execute(
                    ("SELECT id FROM term_aliases WHERE alias_norm = ? AND term_id != ?"),
                    (alias_norm, exclude_term_id),
                ).fetchone()
            else:
                conflict = conn.execute(
                    "SELECT id FROM term_aliases WHERE alias_norm = ?",
                    (alias_norm,),
                ).fetchone()
            if conflict:
                raise ValueError("別名已存在")


def create_term(payload: dict) -> dict:
    _ensure_db()
    term = _normalize_text(payload.get("term"))
    if not term:
        raise ValueError("術語不可為空")
    term_norm = term.lower()
    _check_term_duplicate(term_norm)

    aliases = payload.get("aliases") or []
    alias_norms = [_normalize_text(a).lower() for a in aliases if _normalize_text(a)]
    _check_alias_conflict(alias_norms)

    category_id = _get_or_create_category(
        payload.get("category_id"),
        payload.get("category_name"),
        allow_create=payload.get("allow_create_category", True),
    )
    status = payload.get("status") or "active"
    case_rule = payload.get("case_rule")
    note = payload.get("note")
    created_by = payload.get("created_by")

    with _connect() as conn:
        cur = conn.execute(
            (
                "INSERT INTO terms "
                "(term, term_norm, category_id, status, case_rule, note, source, created_by) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            ),
            (
                term,
                term_norm,
                category_id,
                status,
                case_rule,
                note,
                payload.get("source"),
                created_by,
            ),
        )
        term_id = cur.lastrowid
        _upsert_languages(conn, term_id, payload.get("languages") or [])
        _replace_aliases(conn, term_id, aliases)
        after = _fetch_term_full(conn, term_id)
        _record_version(conn, term_id, before=None, after=after, created_by=created_by)
    return get_term(term_id)


def update_term(term_id: int, payload: dict) -> dict:
    _ensure_db()
    term = _normalize_text(payload.get("term"))
    if not term:
        raise ValueError("術語不可為空")
    term_norm = term.lower()
    _check_term_duplicate(term_norm, exclude_id=term_id)

    aliases = payload.get("aliases") or []
    alias_norms = [_normalize_text(a).lower() for a in aliases if _normalize_text(a)]
    _check_alias_conflict(alias_norms, exclude_term_id=term_id)

    category_id = _get_or_create_category(
        payload.get("category_id"),
        payload.get("category_name"),
        allow_create=payload.get("allow_create_category", True),
    )
    status = payload.get("status") or "active"
    case_rule = payload.get("case_rule")
    note = payload.get("note")

    with _connect() as conn:
        before = _fetch_term_full(conn, term_id)
        conn.execute(
            (
                "UPDATE terms SET term = ?, term_norm = ?, category_id = ?, "
                "status = ?, case_rule = ?, note = ?, source = ?, "
                "updated_at = CURRENT_TIMESTAMP "
                "WHERE id = ?"
            ),
            (term, term_norm, category_id, status, case_rule, note, payload.get("source"), term_id),
        )
        _upsert_languages(conn, term_id, payload.get("languages") or [])
        _replace_aliases(conn, term_id, aliases)
        after = _fetch_term_full(conn, term_id)
        _record_version(
            conn,
            term_id,
            before=before,
            after=after,
            created_by=payload.get("created_by"),
        )
    return get_term(term_id)


def delete_term(term_id: int) -> None:
    _ensure_db()
    with _connect() as conn:
        before = _fetch_term_full(conn, term_id)
        conn.execute("DELETE FROM term_languages WHERE term_id = ?", (term_id,))
        conn.execute("DELETE FROM term_aliases WHERE term_id = ?", (term_id,))
        conn.execute("DELETE FROM terms WHERE id = ?", (term_id,))
        _record_version(conn, term_id, before=before, after=None, created_by=None)


def get_term(term_id: int) -> dict:
    _ensure_db()
    with _connect() as conn:
        term_row = conn.execute(
            (
                "SELECT t.*, c.name AS category_name "
                "FROM terms t "
                "LEFT JOIN categories c ON c.id = t.category_id "
                "WHERE t.id = ?"
            ),
            (term_id,),
        ).fetchone()
        if not term_row:
            raise ValueError("術語不存在")
        term = dict(term_row)
        term["languages"] = _fetch_languages(conn, term_id)
        term["aliases"] = _fetch_aliases(conn, term_id)
    return term


def list_versions(term_id: int) -> list[dict]:
    _ensure_db()
    with _connect() as conn:
        rows = conn.execute(
            (
                "SELECT id, term_id, diff, created_by, created_at "
                "FROM term_versions WHERE term_id = ? "
                "ORDER BY created_at DESC, id DESC"
            ),
            (term_id,),
        ).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        if item.get("diff"):
            try:
                item["diff"] = json.loads(item["diff"])
            except Exception:
                pass
        items.append(item)
    return items


def list_terms(filters: dict) -> list[dict]:  # noqa: C901
    _ensure_db()
    where = []
    params: list = []

    q = _normalize_text(filters.get("q"))
    if q:
        where.append(
            "(t.term_norm LIKE ? OR EXISTS ("
            "SELECT 1 FROM term_aliases a "
            "WHERE a.term_id = t.id AND a.alias_norm LIKE ?"
            "))"
        )
        like = f"%{q.lower()}%"
        params.extend([like, like])

    category_id = filters.get("category_id")
    if category_id:
        where.append("t.category_id = ?")
        params.append(category_id)

    status = filters.get("status")
    if status:
        where.append("t.status = ?")
        params.append(status)

    created_by = _normalize_text(filters.get("created_by"))
    if created_by:
        where.append("t.created_by = ?")
        params.append(created_by)

    source = _normalize_text(filters.get("source"))
    if source:
        where.append("t.source = ?")
        params.append(source)

    date_from = filters.get("date_from")
    if date_from:
        where.append("t.created_at >= ?")
        params.append(date_from)

    date_to = filters.get("date_to")
    if date_to:
        where.append("t.created_at <= ?")
        params.append(date_to)

    missing_lang = filters.get("missing_lang")
    if missing_lang:
        where.append(
            "NOT EXISTS ("
            "SELECT 1 FROM term_languages tl "
            "WHERE tl.term_id = t.id AND tl.lang_code = ? "
            "AND tl.value IS NOT NULL AND tl.value != ''"
            ")"
        )
        params.append(missing_lang)

    has_alias = filters.get("has_alias")
    if has_alias is not None:
        if has_alias:
            where.append("EXISTS (SELECT 1 FROM term_aliases a WHERE a.term_id = t.id)")
        else:
            where.append("NOT EXISTS (SELECT 1 FROM term_aliases a WHERE a.term_id = t.id)")

    clause = " AND ".join(where) if where else "1=1"
    sql = (
        "SELECT t.*, c.name AS category_name "
        "FROM terms t "
        "LEFT JOIN categories c ON c.id = t.category_id "
        f"WHERE {clause} "
        "ORDER BY t.updated_at DESC, t.id DESC"
    )
    with _connect() as conn:
        rows = conn.execute(sql, params).fetchall()
        items = [dict(row) for row in rows]
        for item in items:
            term_id = item["id"]
            item["languages"] = _fetch_languages(conn, term_id)
            item["aliases"] = _fetch_aliases(conn, term_id)
    return items


def batch_update_terms(
    term_ids: list[int],
    category_id: int | None = None,
    status: str | None = None,
    case_rule: str | None = None,
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


def sync_from_external(
    term: str,
    category_name: str | None = None,
    source: str = "manual",
    languages: list[dict] | None = None,
) -> dict:
    """Sync a term from an external source. Merges languages if the term exists."""
    _ensure_db()
    term_text = _normalize_text(term)
    if not term_text:
        return {}

    term_norm = term_text.lower()
    with _connect() as conn:
        row = conn.execute("SELECT id FROM terms WHERE term_norm = ?", (term_norm,)).fetchone()
        term_id = int(row["id"]) if row else None

    if term_id:
        # Existing term, fetch current languages to merge
        with _connect() as conn:
            current_langs = _fetch_languages(conn, term_id)
            lang_dict = {l["lang_code"]: l["value"] for l in current_langs}
            for l in languages or []:
                lang_dict[l["lang_code"]] = l["value"]

            merged_languages = [{"lang_code": k, "value": v} for k, v in lang_dict.items()]

            payload = {
                "term": term_text,
                "category_name": category_name,
                "source": source,
                "languages": merged_languages,
                "status": "active",
            }
            return update_term(term_id, payload)
    else:
        # New term
        payload = {
            "term": term_text,
            "category_name": category_name,
            "source": source,
            "languages": languages or [],
            "status": "active",
            "allow_create_category": True,
        }
        return create_term(payload)


def delete_by_term(term: str) -> None:
    """Delete a term by its text (e.g. from sync hooks)."""
    _ensure_db()
    term_norm = _normalize_text(term).lower()
    with _connect() as conn:
        row = conn.execute("SELECT id FROM terms WHERE term_norm = ?", (term_norm,)).fetchone()
        if row:
            delete_term(int(row["id"]))


def upsert_term_by_norm(payload: dict) -> dict:
    _ensure_db()
    term = _normalize_text(payload.get("term"))
    if not term:
        raise ValueError("術語不可為空")
    term_norm = term.lower()
    with _connect() as conn:
        row = conn.execute(
            "SELECT id FROM terms WHERE term_norm = ?",
            (term_norm,),
        ).fetchone()
    if row:
        return update_term(int(row["id"]), payload)
    return create_term(payload)


def _fetch_languages(conn: sqlite3.Connection, term_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT lang_code, value FROM term_languages WHERE term_id = ?",
        (term_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _fetch_aliases(conn: sqlite3.Connection, term_id: int) -> list[str]:
    rows = conn.execute(
        "SELECT alias FROM term_aliases WHERE term_id = ?",
        (term_id,),
    ).fetchall()
    return [row["alias"] for row in rows]


def _fetch_term_full(conn: sqlite3.Connection, term_id: int) -> dict:
    term_row = conn.execute(
        (
            "SELECT t.*, c.name AS category_name "
            "FROM terms t "
            "LEFT JOIN categories c ON c.id = t.category_id "
            "WHERE t.id = ?"
        ),
        (term_id,),
    ).fetchone()
    if not term_row:
        return {}
    term = dict(term_row)
    term["languages"] = _fetch_languages(conn, term_id)
    term["aliases"] = _fetch_aliases(conn, term_id)
    return term


def _record_version(
    conn: sqlite3.Connection,
    term_id: int,
    before: dict | None,
    after: dict | None,
    created_by: str | None,
) -> None:
    payload = {"before": before, "after": after}
    conn.execute(
        ("INSERT INTO term_versions (term_id, diff, created_by) VALUES (?, ?, ?)"),
        (term_id, json.dumps(payload, ensure_ascii=False), created_by),
    )


def _upsert_languages(conn: sqlite3.Connection, term_id: int, languages: list[dict]) -> None:
    conn.execute("DELETE FROM term_languages WHERE term_id = ?", (term_id,))
    for lang in languages:
        lang_code = _normalize_text(lang.get("lang_code"))
        value = _normalize_text(lang.get("value"))
        if not lang_code:
            continue
        value_norm = value.lower() if value else ""
        conn.execute(
            (
                "INSERT INTO term_languages (term_id, lang_code, value, value_norm) "
                "VALUES (?, ?, ?, ?)"
            ),
            (term_id, lang_code, value, value_norm),
        )


def _replace_aliases(conn: sqlite3.Connection, term_id: int, aliases: list[str]) -> None:
    conn.execute("DELETE FROM term_aliases WHERE term_id = ?", (term_id,))
    for alias in aliases:
        alias_clean = _normalize_text(alias)
        if not alias_clean:
            continue
        alias_norm = alias_clean.lower()
        conn.execute(
            ("INSERT INTO term_aliases (term_id, alias, alias_norm) VALUES (?, ?, ?)"),
            (term_id, alias_clean, alias_norm),
        )
