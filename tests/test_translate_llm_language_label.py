from backend.services.translate_llm import _language_label


def test_language_label_maps_known_codes() -> None:
    assert _language_label("vi") == "Vietnamese (vi)"
    assert _language_label("zh-TW") == "Traditional Chinese (zh-TW)"


def test_language_label_falls_back_to_code() -> None:
    assert _language_label("fr") == "fr"
