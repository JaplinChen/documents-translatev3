from __future__ import annotations


def map_source_lang_to_tesseract(source_lang: str | None) -> str | None:
    if not source_lang:
        return None
    lang = source_lang.strip().lower()
    if not lang or lang == "auto":
        return None
    if lang in {"zh-tw", "zh-hk", "zh-hant", "zh_trad", "zh_traditional"}:
        return "chi_tra"
    if lang in {"zh-cn", "zh-hans", "zh", "zh_sim", "zh_simplified"}:
        return "chi_sim"
    if lang in {"vi", "vie", "vietnamese"}:
        return "vie"
    if lang in {"ja", "jpn", "japanese"}:
        return "jpn"
    if lang in {"ko", "kor", "korean"}:
        return "kor"
    if lang in {"en", "eng", "english"}:
        return "eng"
    return None


def resolve_ocr_lang_from_doc_lang(doc_lang: str | None) -> str | None:
    mapped = map_source_lang_to_tesseract(doc_lang)
    if not mapped:
        return None
    if mapped in {"chi_tra", "chi_sim", "vie", "jpn", "kor"}:
        return f"{mapped}+eng"
    return mapped
