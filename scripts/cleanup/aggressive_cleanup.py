import sqlite3
import re
import os

DB_PATHS = {"tm": "data/translation_memory.db", "terms": "data/terms.db"}


def clean_databases():
    # 1. Patterns to match and delete
    # - Combinations with +
    # - Pure version numbers or models
    # - Generic hardware parts without brand
    # - Long specs
    # - Generic verbs/nouns

    generic_words = {
        "no.",
        "no",
        "none",
        "total",
        "sum",
        "status",
        "date",
        "summary",
        "table",
        "page",
        "index",
        "note",
        "name",
        "type",
        "size",
        "price",
        "quantity",
        "amount",
        "description",
        "item",
        "unit",
        "value",
        "count",
        "number",
        "month",
        "year",
        "day",
        "week",
        "time",
        "file",
        "folder",
        "document",
        "report",
        "list",
        "data",
        "info",
        "detail",
        "ram",
        "bluetooth",
        "projector",
        "keyboard",
        "mouse",
        "monitor",
        "cable",
        "adapter",
        "sửa",
        "xóa",
        "chắc chắn",
        "báo cáo",
        "cải thiện",
        "đề xuất",
    }

    # Combined regex for messy data
    patterns = [
        r".*\+.*",  # Anything with a plus
        r".*,.*",  # Anything with a comma (combo items)
        r"^\d+\s*(pro|plus|max|ultra|lite|oem)$",  # Pure version/models like '10 pro'
        r"^[0-9.]+\s*(GB|TB|GHz|MHz|MB|inch|mm|cm|pcs|kg|m|%)$",  # Pure specs
        r"^(Core|Ryzen|Xeon|RTX|GTX|Geforce|Quadro|AOC|DELL|LG|LENOVO|HP|Acer|Asus|Apple|Intel|AMD|Nvidia|Core|Ultra|Optiplex|MacBook|iPad|iPhone|Galaxy)\s+.*",  # Specific brand items
        r"^[0-9A-F]{2}(:[0-9A-F]{2}){5}$",  # MAC address
        r"^.*[0-9]+\.[0-9]+.*$",  # Software versions like 'FreeCAD 0.17'
        r"^[0-9]+.*$",  # Starts with a number (usually specs or models)
        r"^\(.*\)$",  # Parenthesized like '(GB)'
    ]

    combined_re = re.compile("|".join(patterns), re.IGNORECASE)

    def should_delete(term):
        if not term:
            return True
        term_clean = term.strip()
        term_lower = term_clean.lower()

        # Keep list (explicitly whitelist some terms if needed)
        keep_list = {"windows", "bluetooth", "wifi", "internet", "vpic1", "fpt", "bpm", "uof"}
        if term_lower in keep_list:
            return False

        # Rule 1: Generic words
        if term_lower in generic_words:
            return True

        # Rule 2: Pattern match
        if combined_re.match(term_clean):
            # Special exceptions: keep if it's JUST the brand name (handled by regex ^Brand\s+)
            return True

        # Rule 3: Length/Mess
        if len(term_clean) <= 3 and not term_clean.isupper():
            return True

        # Rule 4: Contains both numbers and letters without space (often model names)
        # But allow common ones like 'Office', 'Windows'
        if any(c.isdigit() for c in term_clean) and any(c.isalpha() for c in term_clean):
            # If it's a long model-like name (e.g. SFG16-72)
            if len(term_clean.split()) == 1 and len(term_clean) > 5:
                return True

        return False

    # Clean translation_memory.db
    print(f"Cleaning {DB_PATHS['tm']}...")
    with sqlite3.connect(DB_PATHS["tm"]) as conn:
        conn.row_factory = sqlite3.Row

        # Cleanup preserve_terms
        rows = conn.execute("SELECT id, term FROM preserve_terms").fetchall()
        to_delete = [row["id"] for row in rows if should_delete(row["term"])]
        print(f"Found {len(to_delete)} problematic terms in preserve_terms")
        for tid in to_delete:
            conn.execute("DELETE FROM preserve_terms WHERE id = ?", (tid,))

        # Cleanup glossary
        rows = conn.execute("SELECT id, source_text FROM glossary").fetchall()
        to_delete = [row["id"] for row in rows if should_delete(row["source_text"])]
        print(f"Found {len(to_delete)} problematic entries in glossary")
        for gid in to_delete:
            conn.execute("DELETE FROM glossary WHERE id = ?", (gid,))
        conn.commit()

    # Clean terms.db
    print(f"Cleaning {DB_PATHS['terms']}...")
    with sqlite3.connect(DB_PATHS["terms"]) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT id, term FROM terms").fetchall()
        to_delete = [row["id"] for row in rows if should_delete(row["term"])]
        print(f"Found {len(to_delete)} problematic terms in terms table")
        for tid in to_delete:
            conn.execute("DELETE FROM terms WHERE id = ?", (tid,))
        conn.commit()


if __name__ == "__main__":
    clean_databases()
    print("Cleanup complete.")
