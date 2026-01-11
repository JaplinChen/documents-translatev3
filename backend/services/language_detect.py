from __future__ import annotations

from collections import Counter
from typing import Iterable

import re

from langdetect import DetectorFactory, LangDetectException, detect

DetectorFactory.seed = 0


LANG_MAP = {
    "zh-cn": "zh-CN",
    "zh-tw": "zh-TW",
    "zh-hk": "zh-TW",
}

_CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")
_VI_DIACRITIC_RE = re.compile(
    r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡ"
    r"ùúụủũưừứựửữỳýỵỷỹđ]"
)
_ZH_TRAD_CHARS = set(
    "體萬與專業經辦應該麼臺灣廣門齊裡發後國點線車書龍這為"
)
_ZH_SIMP_CHARS = set(
    "体万与专业经办应该么台湾广门齐里发后国点线车书龙这为"
)


def _normalize_lang(code: str | None) -> str | None:
    if not code:
        return None
    code = code.lower()
    return LANG_MAP.get(code, code)


def _detect_zh_variant(text: str) -> str:
    trad_score = sum(1 for ch in text if ch in _ZH_TRAD_CHARS)
    simp_score = sum(1 for ch in text if ch in _ZH_SIMP_CHARS)
    if trad_score == 0 and simp_score == 0:
        return "zh-TW"
    return "zh-TW" if trad_score >= simp_score else "zh-CN"


def detect_language(text: str) -> str | None:
    if not text or not text.strip():
        return None
    if _VI_DIACRITIC_RE.search(text.lower()):
        return "vi"
    if _CJK_RE.search(text):
        return _detect_zh_variant(text)
    try:
        lang = _normalize_lang(detect(text))
        if lang == "zh":
            return _detect_zh_variant(text)
        return lang
    except LangDetectException:
        return None


def detect_document_languages(blocks: Iterable[dict]) -> dict:
    counts: Counter[str] = Counter()
    first_line_counts: Counter[str] = Counter()
    second_line_counts: Counter[str] = Counter()
    for block in blocks:
        text = block.get("source_text", "")
        lines = [line for line in text.splitlines() if line.strip()]
        for idx, line in enumerate(lines):
            lang = detect_language(line)
            if not lang:
                continue
            counts[lang] += 1
            if idx == 0:
                first_line_counts[lang] += 1
            if idx == 1:
                second_line_counts[lang] += 1

    if not counts:
        return {"primary": None, "secondary": None, "counts": {}}

    ranked = counts.most_common(2)
    primary = ranked[0][0] if ranked else None
    secondary = ranked[1][0] if len(ranked) > 1 else None

    if first_line_counts and second_line_counts:
        first_lang = first_line_counts.most_common(1)[0][0]
        second_lang = second_line_counts.most_common(1)[0][0]
        if first_lang != second_lang:
            primary = first_lang
            secondary = second_lang
    return {"primary": primary, "secondary": secondary, "counts": dict(counts)}
