from backend.services.llm_prompt import _language_hint

def test_language_hint_vi_mentions_vietnamese() -> None:
    hint = _language_hint("vi")
    assert "越南語" in hint
    assert "Tiếng Việt" in hint
    assert "Solusyon" in hint  # Example of what NOT to output
