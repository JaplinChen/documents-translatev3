from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable
from functools import lru_cache

from langdetect import DetectorFactory, LangDetectException, detect

DetectorFactory.seed = 0


LANG_MAP = {
    "zh-cn": "zh-CN",
    "zh-tw": "zh-TW",
    "zh-hk": "zh-TW",
}

_CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")
_ASCII_ONLY_RE = re.compile(r"^[A-Za-z0-9\s\-\_/\\.,\(\)\[\]{}'\"&:+#%]+$")
_VI_DIACRITIC_RE = re.compile(
    r"["
    r"\u00C0-\u00C3\u00C8-\u00CA\u00CC-\u00CD\u00D2-\u00D5\u00D9-\u00DA\u00DD"
    r"\u00E0-\u00E3\u00E8-\u00EA\u00EC-\u00ED\u00F2-\u00F5\u00F9-\u00FA\u00FD"
    r"\u0102\u0103\u0110\u0111\u0128\u0129\u0168\u0169\u01A0\u01A1\u01AF\u01B0"
    r"\u1EA0-\u1EF9"
    r"]"
)
_ZH_TRAD_CHARS = set(
    "\u9ad4\u842c\u8207\u5c08\u696d\u7d93\u8fa6\u61c9\u8a72\u9ebc\u81fa\u7063"
    "\u5ee3\u9580\u9f4a\u88e1\u767c\u5f8c\u570b\u9ede\u7dda\u8eca\u66f8\u9f8d"
    "\u9019\u70ba"
)
_ZH_SIMP_CHARS = set(
    "\u4f53\u4e07\u4e0e\u4e13\u4e1a\u7ecf\u529e\u5e94\u8be5\u4e48\u53f0\u6e7e"
    "\u5e7f\u95e8\u9f50\u91cc\u53d1\u540e\u56fd\u70b9\u7ebf\u8f66\u4e66\u9f99"
    "\u8fd9\u4e3a"
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


@lru_cache(maxsize=2048)
def detect_language(text: str) -> str | None:
    """偵測文字的語言。

    Uses LRU cache to avoid redundant detections for the same text.

    判斷順序：
    1. 越南語專屬字元（需至少 2 個特徵字元避免誤判）
    2. CJK 字元（中文/日文/韓文）
    3. langdetect 函式庫判斷
    """
    if not text or not text.strip():
        return None

    # 越南語專屬字元：需要至少 2 個特徵字元，避免將 café（法語）誤判為越南語
    # 越南語特有字母：đ, ơ, ư, ă, ê, ô, â 以及帶聲調的組合
    vi_matches = _VI_DIACRITIC_RE.findall(text)
    if len(vi_matches) >= 2:
        return "vi"

    if _CJK_RE.search(text):
        # Return ZH only if CJK characters are a significant portion
        # or if there are no other identifiable language features.
        cjk_count = len(_CJK_RE.findall(text))
        total_len = len(text.strip())
        if cjk_count / total_len > 0.3 or len(text.strip()) < 5:
            return _detect_zh_variant(text)

    ascii_text = text.strip()
    if _ASCII_ONLY_RE.fullmatch(ascii_text):
        alpha_count = len(re.findall(r"[A-Za-z]", ascii_text))
        if alpha_count >= 2:
            return "en"

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

    # Optimization: If too many blocks, sample them to avoid long wait times
    blocks_list = list(blocks)
    if len(blocks_list) > 50:
        # Take first 20, middle 10, last 20
        mid = len(blocks_list) // 2
        sampled_blocks = blocks_list[:20] + blocks_list[mid : mid + 10] + blocks_list[-20:]
    else:
        sampled_blocks = blocks_list

    # Use character counts for better weighting
    char_counts: Counter[str] = Counter()

    for block in sampled_blocks:
        if block.get("block_type") == "image_text":
            continue
        text = block.get("source_text", "")
        lines = [line for line in text.splitlines() if line.strip()]
        for idx, line in enumerate(lines):
            lang = detect_language(line)
            if not lang:
                continue

            # Weighting by length of the line
            weight = len(line.strip())
            counts[lang] += 1
            char_counts[lang] += weight

            if idx == 0:
                first_line_counts[lang] += 1
            if idx == 1:
                second_line_counts[lang] += 1

    if not char_counts:
        return {"primary": None, "secondary": None, "counts": {}}

    # Rank based on character volume instead of block count
    ranked = char_counts.most_common(2)
    primary = ranked[0][0] if ranked else None
    secondary = ranked[1][0] if len(ranked) > 1 else None

    if first_line_counts and second_line_counts:
        first_lang = first_line_counts.most_common(1)[0][0]
        second_lang = second_line_counts.most_common(1)[0][0]
        if first_lang != second_lang:
            primary = first_lang
            secondary = second_lang
    return {"primary": primary, "secondary": secondary, "counts": dict(counts)}


def resolve_source_language(
    blocks: Iterable[dict],
    source_language: str | None,
) -> str | None:
    if source_language and source_language != "auto":
        return source_language
    summary = detect_document_languages(blocks)
    primary = summary.get("primary")
    return primary or None
