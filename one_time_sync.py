import sqlite3
import os

tm_db_path = "data/translation_memory.db"
terms_db_path = "data/terms.db"

# Map old names to new names (based on user's image)
mapping = {
    "專業術語": "專業",
    "產品名稱": "產品",
    "翻譯術語": "翻譯",
    "技術縮寫": "技術",
    "公司名稱": "公司",
    "網絡術語": "網絡"
}

print("Starting one-time sync...")

# 1. Update preserve_terms in translation_memory.db
if os.path.exists(tm_db_path):
    print(f"Updating {tm_db_path}...")
    conn = sqlite3.connect(tm_db_path)
    for old, new in mapping.items():
        conn.execute("UPDATE preserve_terms SET category = ? WHERE category = ?", (new, old))
    conn.commit()
    conn.close()
    print("Updated preserve_terms table.")

# 2. Update categories in terms.db
if os.path.exists(terms_db_path):
    print(f"Updating {terms_db_path}...")
    conn = sqlite3.connect(terms_db_path)
    for old, new in mapping.items():
        conn.execute("UPDATE categories SET name = ? WHERE name = ?", (new, old))
    conn.commit()
    conn.close()
    print("Updated terms.db categories.")

print("Sync complete.")
