import time
import sqlite3
from pathlib import Path

DB_PATH = Path("data/translation_memory.db")
blocks_count = 1386

# Ensure DB exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
with sqlite3.connect(DB_PATH) as conn:
    conn.execute("CREATE TABLE IF NOT EXISTS tm (hash TEXT PRIMARY KEY, target_text TEXT)")


def lookup_tm_mock(text):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("SELECT target_text FROM tm WHERE hash = ?", ("somehash",))
        row = cur.fetchone()
    return None


start = time.perf_counter()
for i in range(blocks_count):
    lookup_tm_mock(f"text {i}")
duration = time.perf_counter() - start

print(f"Queried {blocks_count} blocks in {duration:.4f}s")
print(f"Average: {(duration / blocks_count) * 1000:.4f}ms per query")
