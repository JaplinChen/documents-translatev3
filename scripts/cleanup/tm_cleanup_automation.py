import sqlite3
import re
from pathlib import Path

DB_PATH = Path("data/translation_memory.db")

# 偵測模式
# 1. 型號 + pro/max -> 數字量詞 (如 "7 pro" -> "七個")
MODEL_QUANTIFIER_PATTERN = re.compile(r"^\d+\s*(pro|max|ultra|plus)$", re.IGNORECASE)
QUANTIFIER_CHINESE_PATTERN = re.compile(r"^[一二三四五六七八九十百千萬\d]+[個筆台枝張顆]$")

# 2. 已知誤譯清單 (從截圖中觀察到)
KNOWN_BAD_MAPPINGS = {
    "7 pro": "七個",
    "8 pro": "八個",
    "Core Ultra 5 125H": "核心極致5125H",  # 過度翻譯
}


def cleanup_tm():
    if not DB_PATH.exists():
        print(f"找不到資料庫: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("開始掃描翻譯記憶庫 (TM)...")

    # 獲取所有項目
    cursor.execute("SELECT id, source_text, target_text FROM tm")
    rows = cursor.execute("SELECT id, source_text, target_text FROM tm").fetchall()

    to_delete = []

    for row_id, source, target in rows:
        source_clean = source.strip()
        target_clean = target.strip()

        # 檢查已知壞資料
        if source_clean in KNOWN_BAD_MAPPINGS and KNOWN_BAD_MAPPINGS[source_clean] == target_clean:
            to_delete.append(row_id)
            print(f"  [移除] 已知壞資料: {source_clean} -> {target_clean}")
            continue

        # 檢查模式 1: 型號 -> 量詞 (如 7 pro -> 七個)
        if MODEL_QUANTIFIER_PATTERN.match(source_clean) and QUANTIFIER_CHINESE_PATTERN.match(
            target_clean
        ):
            to_delete.append(row_id)
            print(f"  [移除] 型號量詞誤譯: {source_clean} -> {target_clean}")
            continue

        # 檢查模式 2: 過度翻譯的 CPU 型號 (如 Core Ultra -> 核心極致)
        if "Core Ultra" in source_clean and "核心極致" in target_clean:
            to_delete.append(row_id)
            print(f"  [移除] CPU 過度翻譯: {source_clean} -> {target_clean}")
            continue

    if to_delete:
        print(f"總計將移除 {len(to_delete)} 筆資料...")
        cursor.executemany("DELETE FROM tm WHERE id = ?", [(rid,) for rid in to_delete])
        conn.commit()
        print("清理完成！")
    else:
        print("未偵測到明顯的髒資料。")

    conn.close()


if __name__ == "__main__":
    cleanup_tm()
