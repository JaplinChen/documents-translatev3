from backend.services.translate_config import get_language_label

def test_language_label_maps_known_codes() -> None:
    assert get_language_label("vi") == "Vietnamese (vi)"
    assert get_language_label("zh-TW") == "Traditional Chinese (zh-TW)"


def test_language_label_falls_back_to_code() -> None:
    assert get_language_label("fr") == "fr"
