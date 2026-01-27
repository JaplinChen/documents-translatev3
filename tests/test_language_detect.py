from backend.services.language_detect import detect_language, resolve_source_language

def test_resolve_source_language_prefers_explicit() -> None:
    blocks = [{"source_text": "Hello"}]
    assert resolve_source_language(blocks, "en") == "en"


def test_resolve_source_language_auto_detects_primary() -> None:
    blocks = [{"source_text": "這是一段中文"}]
    assert resolve_source_language(blocks, "auto") == "zh-TW"


def test_resolve_source_language_none_returns_detected() -> None:
    blocks = [{"source_text": "Xin chào"}]
    assert resolve_source_language(blocks, None) == "vi"


def test_detect_language_cafe_not_vietnamese() -> None:
    """單一變音符（如 café）不應被誤判為越南語。"""
    # café 只有一個變音符 é，不應判為越南語
    result = detect_language("café")
    assert result != "vi", f"Expected non-Vietnamese, got: {result}"


def test_detect_language_vietnamese_needs_multiple_diacritics() -> None:
    """越南語需要至少 2 個特徵字元才會被判斷。"""
    # Xin chào 有 2 個越南語特徵（à, o hook）
    result = detect_language("Xin chào Việt Nam")
    assert result == "vi", f"Expected 'vi', got: {result}"
