from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import threading
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class DocumentCache:
    _instance: DocumentCache | None = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.db_path = Path("data/cache.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._initialized = True

    def _init_db(self) -> None:
        query = """
        CREATE TABLE IF NOT EXISTS document_cache (
            file_hash TEXT PRIMARY KEY,
            blocks_json TEXT,
            metadata_json TEXT,
            file_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        try:
            with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                conn.execute(query)
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_doc_cache_hash ON document_cache(file_hash)"
                )
        except Exception as err:
            LOGGER.error("DocumentCache init error: %s", err)

    def get_hash(self, file_bytes: bytes) -> str:
        """計算文件的 SHA-256 雜湊值。"""
        return hashlib.sha256(file_bytes).hexdigest()

    def get(self, file_hash: str) -> dict | None:
        """根據雜湊值從快取獲取資料。"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT blocks_json, metadata_json FROM document_cache WHERE file_hash = ?",
                    (file_hash,),
                )
                row = cursor.fetchone()
                if row:
                    return {"blocks": json.loads(row[0]), "metadata": json.loads(row[1])}
                return None
        except Exception as err:
            LOGGER.error("DocumentCache get error: %s", err)
            return None

    def set(self, file_hash: str, blocks: list[dict], metadata: dict, file_type: str) -> None:
        """將提取結果存入快取。"""
        try:
            query = (
                "INSERT OR REPLACE INTO document_cache "
                "(file_hash, blocks_json, metadata_json, file_type) "
                "VALUES (?, ?, ?, ?)"
            )
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    query,
                    (
                        file_hash,
                        json.dumps(blocks, ensure_ascii=False),
                        json.dumps(metadata, ensure_ascii=False),
                        file_type,
                    ),
                )
        except Exception as err:
            LOGGER.error("DocumentCache set error: %s", err)

    def update_metadata(self, file_hash: str, updates: dict) -> None:
        """更新快取中的元數據。"""
        try:
            current = self.get(file_hash)
            if not current:
                return

            metadata = current["metadata"]
            metadata.update(updates)

            query = "UPDATE document_cache SET metadata_json = ? WHERE file_hash = ?"
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    query,
                    (json.dumps(metadata, ensure_ascii=False), file_hash),
                )
        except Exception as err:
            LOGGER.error("DocumentCache update_metadata error: %s", err)


# 單例模式出口
doc_cache = DocumentCache()
