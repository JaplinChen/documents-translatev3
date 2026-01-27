import re

def _is_numeric_only(text: str) -> bool:
    """Check if the text is only numbers, punctuation, or whitespace."""
    if not text.strip():
        return True
    # If it contains any letter (English, CJK), it's not numeric-only.
    if re.search(r"[a-zA-Z\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]", text):
        return False
    return True


test_cases = [
    ("123", True),
    ("1,000.00", True),
    ("2024-01-01", True),
    ("10%", True),
    ("$100", True),
    (" ", True),
    ("", True),
    ("Page 1", False),
    ("第 1 頁", False),
    ("Hello 123", False),
    ("こんにちは", False),
    ("123abc", False),
]

for text, expected in test_cases:
    result = _is_numeric_only(text)
    print(f"Text: '{text}' -> Result: {result} (Expected: {expected})")
    assert result == expected

print("\nAll tests passed!")
