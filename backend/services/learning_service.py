from __future__ import annotations
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from backend.services.translation_memory import DB_PATH, _ensure_db

LOGGER = logging.getLogger(__name__)


def record_term_feedback(
    source_text: str,
    target_text: str,
    source_lang: str | None = None,
    target_lang: str | None = "zh-TW",
) -> None:
    """
    紀錄用戶對特定單詞/片語的修正行為。
    如果該組合已存在，則增加修正次數 (correction_count)。
    """
    _ensure_db()
    if not source_text or not target_text:
        return

    query = """
    INSERT INTO term_feedback (source_text, target_text, source_lang, target_lang, correction_count, last_corrected_at)
    VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
    ON CONFLICT(source_text, target_text, source_lang, target_lang) DO UPDATE SET
        correction_count = correction_count + 1,
        last_corrected_at = CURRENT_TIMESTAMP
    """
    try:
        with sqlite3.connect(DB_PATH, timeout=10) as conn:
            conn.execute(
                query, (source_text.strip(), target_text.strip(), source_lang, target_lang)
            )
            conn.commit()

            # --- 自動進化：若修正次數達標，自動寫入對照表 ---
            cursor = conn.execute(
                "SELECT correction_count FROM term_feedback WHERE source_text = ? AND target_text = ? AND source_lang = ? AND target_lang = ?",
                (source_text.strip(), target_text.strip(), source_lang, target_lang),
            )
            row = cursor.fetchone()
            if row and row[0] >= 3:
                from backend.services.translation_memory import upsert_glossary

                LOGGER.info(
                    f"Auto-promoting to glossary: {source_text} -> {target_text} (count: {row[0]})"
                )
                upsert_glossary(
                    {
                        "source_lang": source_lang or "auto",
                        "target_lang": target_lang or "zh-TW",
                        "source_text": source_text.strip(),
                        "target_text": target_text.strip(),
                        "priority": 10,  # 自動學習的權重設為最高
                        "category_id": None,
                    }
                )
    except Exception as e:
        LOGGER.error(f"Failed to record term feedback: {e}")


def get_learned_terms(
    target_lang: str = "zh-TW", min_count: int = 1, limit: int = 50
) -> list[dict]:
    """
    獲取系統已學習到的高頻修正術語。
    """
    _ensure_db()
    query = """
    SELECT source_text, target_text, correction_count 
    FROM term_feedback 
    WHERE target_lang = ? 
    ORDER BY correction_count DESC, last_corrected_at DESC
    LIMIT ?
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute(query, (target_lang, limit))
            rows = cursor.fetchall()
            return [
                {"source": r[0], "target": r[1], "count": r[2]} for r in rows if r[2] >= min_count
            ]
    except Exception as e:
        LOGGER.error(f"Failed to get learned terms: {e}")
        return []


def detect_domain(text_sample: str) -> str:
    """
    根據文本內容初步判斷領域類型 (Domain)。
    後續可整合至 LLM 判斷，目前先採用關鍵字命中法作為 Baseline。
    """
    if not text_sample:
        return "general"

    domains = {
        "it": ["software", "hardware", "cpu", "model", "server", "api", "code"],
        "medical": ["hospital", "patient", "treatment", "doctor", "drug", "clinic"],
        "legal": ["contract", "agreement", "party", "law", "court", "compliance"],
        "finance": ["revenue", "cost", "investment", "stock", "margin", "budget"],
    }

    text_lower = text_sample.lower()
    scores = {d: 0 for d in domains}
    for domain, keywords in domains.items():
        for kw in keywords:
            if kw in text_lower:
                scores[domain] += 1

    max_domain = max(scores, key=scores.get)
    return max_domain if scores[max_domain] > 0 else "general"
