from backend.services.extract_utils import is_technical_terms_only
from backend.services.glossary_extraction import _validate_and_filter_terms
from backend.services.translation_memory import upsert_tm
import sqlite3
from pathlib import Path


def test_extract_utils():
    print("Testing extract_utils.is_technical_terms_only...")
    test_cases = [
        ("SFG16-71", True),
        ("SN: 12345678", True),
        ("MAC: 00-11-22-33-44-55", True),
        ("IP: 192.168.1.1", True),
        ("v1.2.3", True),
        ("Normal Word", False),
        ("公司名稱", False),
    ]
    for text, expected in test_cases:
        result = is_technical_terms_only(text)
        print(f"  '{text}' -> {result} (Expected: {expected})")
        assert result == expected


def test_glossary_filtering():
    print("\nTesting glossary_extraction._validate_and_filter_terms...")
    existing = set()
    terms = [
        {
            "source": "Windows 11 + Office 2021",
            "target": "Windows 11 + Office 2021",
            "category": "technical",
            "confidence": 10,
        },
        {"source": "Serial Number", "target": "序號", "category": "technical", "confidence": 10},
        {"source": "SFG16-72", "target": "SFG16-72", "category": "technical", "confidence": 10},
        {
            "source": "Translatable Term",
            "target": "可翻譯詞彙",
            "category": "technical",
            "confidence": 10,
        },
    ]
    filtered = _validate_and_filter_terms(terms, existing)
    sources = [f["source"] for f in filtered]
    print(f"  Filtered sources: {sources}")
    # Windows 11 + Office 2021 should be skipped (combination > 2 words)
    # Serial Number should be skipped (GENERIC_WORDS / SN prefix)
    # SFG16-72 should be skipped (source == target identity filter)
    expected_sources = ["Translatable Term"]
    assert "Translatable Term" in sources
    assert "SFG16-72" not in sources
    assert "Windows 11 + Office 2021" not in sources


def test_tm_skipping():
    print("\nTesting translation_memory.upsert_tm skipping...")
    # This might print "Skipping redundant TM entry" to console
    entry = {
        "source_text": "SFG16-72",
        "target_text": "SFG16-72",
        "source_lang": "en",
        "target_lang": "zh-TW",
    }
    upsert_tm(entry)
    # We can't easily check the DB without side effects here, but we can verify it doesn't crash
    # and we saw the logic in the code.


if __name__ == "__main__":
    try:
        test_extract_utils()
        test_glossary_filtering()
        test_tm_skipping()
        print("\nAll tests passed!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback

        traceback.print_exc()
