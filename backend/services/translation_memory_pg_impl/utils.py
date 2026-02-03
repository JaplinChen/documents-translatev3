from __future__ import annotations

import hashlib
import re


def _hash_text(
    source_lang: str,
    target_lang: str,
    text_value: str,
    context: dict | None = None,
) -> str:
    payload = f"{source_lang}|{target_lang}|{text_value}"
    if context:
        ctx_str = "|".join(str(context.get(k, "")) for k in ["provider", "model", "tone"])
        payload += f"||{ctx_str}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalize_glossary_text(text_value: str | None) -> str:
    if not text_value:
        return ""
    return " ".join(text_value.strip().split())


def _resolve_context_scope(context: dict | None) -> tuple[str, str | None, str | None, str | None]:
    if not context:
        return "project", "default", None, None
    scope_type = context.get("scope_type") or "project"
    scope_id = context.get("scope_id") or "default"
    domain = context.get("domain")
    category = context.get("category")
    return scope_type, scope_id, domain, category


def _is_low_quality_tm(source: str, target: str) -> bool:
    """檢查是否為低質量的翻譯記憶條目（如型號轉量詞）。"""
    s = source.strip()
    t = target.strip()

    # 模式 A: 原文等於譯文且為純西方字符 (IT 代碼/型號)
    if s.lower() == t.lower():
        if not re.search(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]", s):
            return True

    # 模式 B: 原文為型號 (數字 + pro/max 等) 而譯文為中文量詞 (如 7 pro -> 七個)
    model_pattern = r"^\d+\s*(pro|max|ultra|plus|s|ti|fe)$"
    quantifier_pattern = r"^[一二三四五六七八九十百千萬\d]+[個筆台枝張顆]$"
    if re.match(model_pattern, s, re.IGNORECASE) and re.match(quantifier_pattern, t):
        return True

    # 模式 C: 著名的 CPU 過度翻譯
    if "Core Ultra" in s and "核心極致" in t:
        return True

    return False
