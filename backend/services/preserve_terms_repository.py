from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from uuid import uuid4

DB_PATH = Path("data/translation_memory.db")
LEGACY_FILES = [
    Path(__file__).parent.parent / "data" / "preserve_terms.json",
    Path("data/preserve_terms.json"),
]

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS preserve_terms (
  id TEXT PRIMARY KEY,
  term TEXT NOT NULL UNIQUE,
  category TEXT NOT NULL DEFAULT '未分類',
  case_sensitive INTEGER NOT NULL DEFAULT 1,
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
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_preserve_terms_term "
            "ON preserve_terms(term)"
        )
    _migrate_from_json()
    _DB_INITIALIZED = True


def _migrate_from_json() -> None:
    _ensure_db_state = DB_PATH.exists()
    if not _ensure_db_state:
        return
    with _connect() as conn:
        row = conn.execute("SELECT COUNT(1) AS cnt FROM preserve_terms").fetchone()
        if row and int(row["cnt"] or 0) > 0:
            return
    for legacy_path in LEGACY_FILES:
        if not legacy_path.exists():
            continue
        try:
            data = json.loads(legacy_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, list):
            continue
        for entry in data:
            term = (entry.get("term") or "").strip()
            if not term:
                continue
            payload = {
                "id": entry.get("id") or str(uuid4()),
                "term": term,
                "category": (entry.get("category") or "未分類").strip(),
                "case_sensitive": bool(entry.get("case_sensitive", True)),
                "created_at": entry.get("created_at") or datetime.utcnow().isoformat() + "Z",
            }
            try:
                with _connect() as conn:
                    conn.execute(
                        (
                            "INSERT OR IGNORE INTO preserve_terms "
                            "(id, term, category, case_sensitive, created_at) "
                            "VALUES (?, ?, ?, ?, ?)"
                        ),
                        (
                            payload["id"],
                            payload["term"],
                            payload["category"],
                            1 if payload["case_sensitive"] else 0,
                            payload["created_at"],
                        ),
                    )
                    conn.commit()
            except Exception:
                continue


def list_preserve_terms() -> list[dict]:
    _ensure_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, term, category, case_sensitive, created_at "
            "FROM preserve_terms ORDER BY created_at DESC, term ASC"
        ).fetchall()
    return [
        {
            "id": row["id"],
            "term": row["term"],
            "category": row["category"],
            "case_sensitive": bool(row["case_sensitive"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def create_preserve_term(
    term: str,
    category: str = "未分類",
    case_sensitive: bool = True,
) -> dict:
    _ensure_db()
    term_text = (term or "").strip()
    if not term_text:
        raise ValueError("術語不可為空")
    with _connect() as conn:
        existing = conn.execute(
            "SELECT id FROM preserve_terms WHERE lower(term) = lower(?)",
            (term_text,),
        ).fetchone()
        if existing:
            raise ValueError(f"術語 '{term_text}' 已存在")
        term_id = str(uuid4())
        created_at = datetime.utcnow().isoformat() + "Z"
        conn.execute(
            (
                "INSERT INTO preserve_terms "
                "(id, term, category, case_sensitive, created_at) "
                "VALUES (?, ?, ?, ?, ?)"
            ),
            (term_id, term_text, category or "未分類", 1 if case_sensitive else 0, created_at),
        )
        conn.commit()
    return {
        "id": term_id,
        "term": term_text,
        "category": category or "未分類",
        "case_sensitive": case_sensitive,
        "created_at": created_at,
    }


def create_preserve_terms_batch(terms: list[dict]) -> dict:
    _ensure_db()
    created = 0
    skipped = 0
    created_terms: list[dict] = []
    with _connect() as conn:
        existing = {
            row["term"].lower()
            for row in conn.execute("SELECT term FROM preserve_terms").fetchall()
        }
        for entry in terms:
            term_text = (entry.get("term") or "").strip()
            if not term_text:
                continue
            key = term_text.lower()
            if key in existing:
                skipped += 1
                continue
            term_id = str(uuid4())
            created_at = datetime.utcnow().isoformat() + "Z"
            category = (entry.get("category") or "未分類").strip()
            case_sensitive = bool(entry.get("case_sensitive", True))
            conn.execute(
                (
                    "INSERT INTO preserve_terms "
                    "(id, term, category, case_sensitive, created_at) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                (term_id, term_text, category, 1 if case_sensitive else 0, created_at),
            )
            created += 1
            created_terms.append(
                {
                    "id": term_id,
                    "term": term_text,
                    "category": category,
                    "case_sensitive": case_sensitive,
                    "created_at": created_at,
                }
            )
            existing.add(key)
        conn.commit()
    return {"created": created, "skipped": skipped, "terms": created_terms}


def update_preserve_term(
    term_id: str,
    term: str,
    category: str = "未分類",
    case_sensitive: bool = True,
) -> dict:
    _ensure_db()
    term_text = (term or "").strip()
    if not term_text:
        raise ValueError("術語不可為空")
    with _connect() as conn:
        row = conn.execute(
            "SELECT id FROM preserve_terms WHERE id = ?",
            (term_id,),
        ).fetchone()
        if not row:
            raise ValueError("術語不存在")
        conflict = conn.execute(
            "SELECT id FROM preserve_terms WHERE lower(term) = lower(?) AND id != ?",
            (term_text, term_id),
        ).fetchone()
        if conflict:
            raise ValueError(f"術語 '{term_text}' 已存在")
        conn.execute(
            "UPDATE preserve_terms SET term = ?, category = ?, case_sensitive = ? WHERE id = ?",
            (term_text, category or "未分類", 1 if case_sensitive else 0, term_id),
        )
        conn.commit()
    return {
        "id": term_id,
        "term": term_text,
        "category": category or "未分類",
        "case_sensitive": case_sensitive,
    }


def delete_preserve_term(term_id: str) -> dict:
    _ensure_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, term, category, case_sensitive, created_at "
            "FROM preserve_terms WHERE id = ?",
            (term_id,),
        ).fetchone()
        if not row:
            raise ValueError("術語不存在")
        conn.execute("DELETE FROM preserve_terms WHERE id = ?", (term_id,))
        conn.commit()
    return {
        "id": row["id"],
        "term": row["term"],
        "category": row["category"],
        "case_sensitive": bool(row["case_sensitive"]),
        "created_at": row["created_at"],
    }


def delete_all_preserve_terms() -> None:
    _ensure_db()
    with _connect() as conn:
        conn.execute("DELETE FROM preserve_terms")
        conn.commit()


def get_preserve_term_by_id(term_id: str) -> dict | None:
    _ensure_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, term, category, case_sensitive, created_at "
            "FROM preserve_terms WHERE id = ?",
            (term_id,),
        ).fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "term": row["term"],
        "category": row["category"],
        "case_sensitive": bool(row["case_sensitive"]),
        "created_at": row["created_at"],
    }
