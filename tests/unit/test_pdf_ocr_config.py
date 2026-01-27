
from backend.services.pdf import extract as pdf_extract

def test_get_ocr_config_defaults(monkeypatch):
    monkeypatch.delenv("PDF_OCR_DPI", raising=False)
    monkeypatch.delenv("PDF_OCR_LANG", raising=False)
    monkeypatch.delenv("PDF_OCR_CONF_MIN", raising=False)

    config = pdf_extract.get_ocr_config()

    assert config["dpi"] == 200
    assert config["lang"] == "eng"
    assert config["conf_min"] == 10


def test_get_ocr_config_overrides(monkeypatch):
    monkeypatch.setenv("PDF_OCR_DPI", "300")
    monkeypatch.setenv("PDF_OCR_LANG", "chi_tra+vie+eng")
    monkeypatch.setenv("PDF_OCR_CONF_MIN", "25")

    config = pdf_extract.get_ocr_config()

    assert config["dpi"] == 300
    assert config["lang"] == "chi_tra+vie+eng"
    assert config["conf_min"] == 25
