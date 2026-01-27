import re

import pytest

def _is_numeric_only(text: str) -> bool:
    if not text.strip():
        return True
    if re.search(r"[a-zA-Z\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]", text):
        return False
    return True


def _is_technical_terms_only(text: str) -> bool:
    if not text.strip():
        return True
    cleaned = re.sub(r"[,、，/\s]+", " ", text).strip()
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
    if len(words) <= 10:
        # Support: SOP (Caps), Notion (Title), wiki (lower), GraphQL/gRPC.
        technical_pattern = r"^[a-zA-Z][a-zA-Z0-9]*$"
        if all(re.match(technical_pattern, word) for word in words):
            return True
    return False


@pytest.mark.parametrize(
    "text, expected",
    [
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
    ],
)
def test_is_numeric_only(text, expected):
    assert _is_numeric_only(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Notion", True),
        ("Obsidian", True),
        ("Wiki, SOP, CRM", True),
        ("API", True),
        ("REST, GraphQL, gRPC", True),
        ("This is a sentence with Notion", False),
        ("使用 SOP 進行管理", False),
    ],
)
def test_is_technical_terms_only(text, expected):
    assert _is_technical_terms_only(text) == expected
