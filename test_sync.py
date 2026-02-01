from backend.services.term_repository import sync_from_external, _connect
import sqlite3

try:
    res = sync_from_external(
        "TestTerm",
        source="reference",
        languages=[{"lang_code": "en", "value": "TestValue"}]
    )
    print("Sync Result:", res.get('id'))
    
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM term_languages WHERE term_id = ?", (res['id'],)).fetchall()
        print("Languages in DB:", [dict(r) for r in rows])
except Exception as e:
    print("Error:", e)
