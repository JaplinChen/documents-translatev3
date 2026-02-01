import re


# Mocking the functions to test logic in isolation
def is_technical_terms_only_mock(text: str) -> bool:
    if not text or not text.strip():
        return True

    text_clean = text.strip()

    # Skip common IT prefixes (Check BEFORE normalization)
    SKIP_PREFIXES = (
        r"^(ID|UUID|SN|PN|IP|MAC|No|No\.|S/N|P/N|ID\s+No|Item\s+No|Part\s+No|Serial\s+No)[:：\s]"
    )
    if re.search(SKIP_PREFIXES, text_clean, re.IGNORECASE):
        return True

    cleaned = re.sub(r"[,、，/\s]+", " ", text_clean).strip()

    if re.search(r"[\u4e00-\u9fff\u3040-\u30ff\u0e00-\u0e7f]", cleaned):
        return False

    sentence_indicators = (
        r"\b(the|a|an|is|are|was|were|be|have|has|had|do|does|did|"
        r"will|would|can|could|should|may|might|must|please|this|"
        r"that|these|those|with|from|to|in|on|at|for|of|and|or|but)\b"
    )
    if re.search(sentence_indicators, cleaned, re.IGNORECASE):
        return False

    words = cleaned.split()
    word_count = len(words)
    if word_count > 10:
        return False

    is_all_caps_or_id = all(
        (re.match(r"^[#A-Z0-9_\-]+$", w) or re.match(r"^#\d+$", w)) and len(w) <= 30 for w in words
    )
    is_mixed_case = all(re.match(r"^[A-Z][a-z]*[A-Z][a-zA-Z]*$", w) and len(w) <= 30 for w in words)
    is_mac = any(re.match(r"^[0-9A-F]{2}([:\-][0-9A-F]{2}){5}$", w, re.IGNORECASE) for w in words)
    is_ip = any(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", w) for w in words)
    is_version = any(re.match(r"^v?\d+(\.\d+){1,3}$", w, re.IGNORECASE) for w in words)

    if is_all_caps_or_id or is_mixed_case or is_mac or is_ip or is_version:
        return True
    return False


def test_isolated_logic():
    print("Testing isolated IT filter logic (v2)...")
    test_cases = [
        ("SFG16-71", True),
        ("SN: 12345678", True),
        ("MAC: 00-11-22-33-44-55", True),
        ("IP: 192.168.1.1", True),
        ("v1.2.3", True),
        ("P/N: ABC-123", True),
        ("No. 123", True),
        ("Normal Word", False),
        ("Company Name", False),
    ]
    for text, expected in test_cases:
        result = is_technical_terms_only_mock(text)
        print(f"  '{text}' -> {result} (Expected: {expected})")
        assert result == expected


if __name__ == "__main__":
    test_isolated_logic()
    print("\nIsolated logic tests passed!")
