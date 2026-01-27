from backend.services.extract_utils import is_numeric_only, is_technical_terms_only

def test_is_numeric_only_happy_path():
    assert is_numeric_only("123.45") is True
    assert is_numeric_only("2024-01-01") is True
    assert is_numeric_only("1,234.56%") is True
    assert is_numeric_only("   ") is True

def test_is_numeric_only_edge_cases():
    assert is_numeric_only(None) is True
    assert is_numeric_only("Price: 100") is False # Contains English letters
    assert is_numeric_only("価格") is False # Contains Japanese
    assert is_numeric_only("123 Main St.") is False

def test_is_technical_terms_only_happy_path():
    # Terms that look like technical identifiers
    assert is_technical_terms_only("API_KEY") is True
    assert is_technical_terms_only("JSON_DATA_V1") is True
    assert is_technical_terms_only("AppId") is True # MixedCase

def test_is_technical_terms_only_edge_cases():
    assert is_technical_terms_only(None) is True
    assert is_technical_terms_only("") is True
    assert is_technical_terms_only("This is a normal sentence.") is False
    assert is_technical_terms_only("你好世界") is False # CJK characters

    # Very long strings should not be technical terms
    long_str = "A" * 50
    assert is_technical_terms_only(long_str) is False

    # Common words should not be technical terms (filtered by sentence_indicators)
    assert is_technical_terms_only("the") is False
