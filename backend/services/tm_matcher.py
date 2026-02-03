from __future__ import annotations

import re
import unicodedata
from typing import Iterable, List, Tuple


def normalize_text(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\u2010-\u2015]", "-", text)
    text = re.sub(r"[\\s\\u00a0]+", " ", text)
    return text


def tokenize(text: str) -> List[str]:
    return [tok for tok in re.split(r"[^\\w]+", text) if tok]


def jaccard(tokens_a: Iterable[str], tokens_b: Iterable[str]) -> float:
    set_a = set(tokens_a)
    set_b = set(tokens_b)
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def edit_distance(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            curr.append(min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def compute_match_score(query: str, candidate: str, domain_bonus: float) -> float:
    q = normalize_text(query)
    c = normalize_text(candidate)
    if q == c:
        return min(1.0, 0.96 + min(0.04, domain_bonus))
    token_overlap = jaccard(tokenize(q), tokenize(c))
    max_len = max(len(q), len(c), 1)
    char_similarity = 1.0 - (edit_distance(q, c) / max_len)
    length_ratio = min(len(q), len(c)) / max_len
    score = (
        0.40 * token_overlap
        + 0.35 * char_similarity
        + 0.15 * length_ratio
        + 0.10 * domain_bonus
    )
    if token_overlap >= 0.5 and length_ratio >= 0.5:
        score += 0.25
    elif token_overlap >= 0.33 and length_ratio >= 0.5:
        score += 0.15
    return max(0.0, min(score, 1.0))


def fuzzy_match(
    query: str,
    candidates: Iterable[dict],
    scope: dict,
    min_score: float = 0.78,
    limit: int = 3,
) -> List[Tuple[float, dict]]:
    results: List[Tuple[float, dict]] = []
    for item in candidates:
        domain_bonus = 0.0
        if item.get("domain") and scope.get("domain") and item["domain"] == scope["domain"]:
            domain_bonus += 0.05
        if item.get("category") and scope.get("category") and item["category"] == scope["category"]:
            domain_bonus += 0.05

        score = compute_match_score(query, item.get("source_text", ""), domain_bonus)
        if item.get("scope_type") != scope.get("scope_type") or item.get("scope_id") != scope.get(
            "scope_id"
        ):
            score -= 0.05

        if score >= min_score:
            results.append((score, item))

    results.sort(key=lambda x: x[0], reverse=True)
    return results[:limit]
