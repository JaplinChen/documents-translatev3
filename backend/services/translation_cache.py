from __future__ import annotations

import hashlib
import logging
import sqlite3
import threading
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class TranslationCache:
    _instance: TranslationCache | None = None
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
        CREATE TABLE IF NOT EXISTS translation_cache (
            key TEXT PRIMARY KEY,
            translated_text TEXT,
            provider TEXT,
            model TEXT,
            target_lang TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
            conn.execute(query)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cache_key "
                "ON translation_cache(key)"
            )

    def _make_key(
        self,
        source_text: str,
        target_lang: str,
        provider: str,
        model: str,
        tone: str | None = None,
        vision_context: bool = True,
    ) -> str:
        raw_key = (
            f"{source_text}|{target_lang}|{provider}|{model}|"
            f"{tone or ''}|{vision_context}"
        )
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def get(
        self,
        source_text: str,
        target_lang: str,
        provider: str,
        model: str,
        tone: str | None = None,
        vision_context: bool = True,
    ) -> str | None:
        key = self._make_key(
            source_text,
            target_lang,
            provider,
            model,
            tone,
            vision_context,
        )
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT translated_text FROM translation_cache "
                    "WHERE key = ?",
                    (key,),
                )
                row = cursor.fetchone()
                return row[0] if row else None
        except Exception as err:
            LOGGER.error("Cache get error: %s", err)
            return None

    def set(
        self,
        source_text: str,
        target_lang: str,
        provider: str,
        model: str,
        translated_text: str,
        tone: str | None = None,
        vision_context: bool = True,
    ) -> None:
        if not translated_text:
            return
        key = self._make_key(
            source_text,
            target_lang,
            provider,
            model,
            tone,
            vision_context,
        )
        query = (
            "INSERT OR REPLACE INTO translation_cache "
            "(key, translated_text, provider, model, target_lang) "
            "VALUES (?, ?, ?, ?, ?)"
        )
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    query,
                    (key, translated_text, provider, model, target_lang),
                )
        except Exception as err:
            LOGGER.error("Cache set error: %s", err)


# Singleton
cache = TranslationCache()
