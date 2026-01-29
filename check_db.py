import sqlite3
import os

tm_db_path = "data/translation_memory.db"
terms_db_path = "data/terms.db"

def check_db(db):
    if os.path.exists(db):
        print(f"--- {db} ---")
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        
        # List tables
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        for t in tables:
            tname = t['name']
            if tname in ['tm_categories', 'categories', 'preserve_terms']:
                print(f"\nTable: {tname}")
                rows = conn.execute(f"SELECT * FROM {tname} LIMIT 10").fetchall()
                for row in rows:
                    print(dict(row))
            
            if tname == 'glossary':
                print(f"\nSample {tname}:")
                rows = conn.execute("SELECT g.id, g.source_text, c.name FROM glossary g JOIN tm_categories c ON g.category_id=c.id LIMIT 3").fetchall()
                for row in rows:
                    print(dict(row))
        conn.close()

check_db(tm_db_path)
check_db(terms_db_path)
