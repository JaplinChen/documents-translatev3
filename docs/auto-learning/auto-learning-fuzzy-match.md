# TM fuzzy/partial match 設計與測試

本文件提供 fuzzy/partial match 的實作偽碼與測試案例，與規格中的分數與門檻一致。

## 核心規則
- 查詢優先序：Exact -> Normalized exact -> Fuzzy/partial
- 僅回傳 `match_score >= 0.78` 的前 3 筆
- `scope` 不同時分數 -0.05（避免跨 scope 汙染）
- 同 domain +0.05、同 category +0.05（上限 0.10）

## 演算法偽碼（Python）
```python
def normalize_text(text: str) -> str:
    text = text.strip()
    text = text.lower()
    text = normalize_punct(text)        # 標點正規化
    text = normalize_width(text)        # 全半形正規化
    return text


def compute_match_score(query: str, candidate: str, domain_bonus: float) -> float:
    q = normalize_text(query)
    c = normalize_text(candidate)

    token_overlap = jaccard(tokenize(q), tokenize(c))          # 0~1
    char_similarity = 1.0 - edit_distance(q, c) / max(len(q), len(c), 1)
    length_ratio = min(len(q), len(c)) / max(len(q), len(c), 1)

    score = (
        0.40 * token_overlap
        + 0.35 * char_similarity
        + 0.15 * length_ratio
        + 0.10 * domain_bonus
    )
    return max(0.0, min(score, 1.0))


def fuzzy_match(query, candidates, scope, min_score=0.78, limit=3):
    results = []
    for item in candidates:
        domain_bonus = 0.0
        if item.domain == scope.domain:
            domain_bonus += 0.05
        if item.category == scope.category:
            domain_bonus += 0.05

        score = compute_match_score(query, item.source_text, domain_bonus)
        if item.scope_type != scope.scope_type or item.scope_id != scope.scope_id:
            score -= 0.05

        if score >= min_score:
            results.append((score, item))

    results.sort(key=lambda x: x[0], reverse=True)
    return results[:limit]
```

## 測試案例（pytest 範例）
```python
def test_fuzzy_exact_match():
    score = compute_match_score("Database migration", "Database migration", 0.0)
    assert score >= 0.95


def test_fuzzy_normalized_match():
    score = compute_match_score("API-Server", "api server", 0.0)
    assert score >= 0.85


def test_fuzzy_partial_match():
    score = compute_match_score("User profile update", "Update profile", 0.05)
    assert score >= 0.78


def test_fuzzy_scope_penalty():
    score = compute_match_score("Cache invalidation", "Cache invalidation", 0.0) - 0.05
    assert score >= 0.90


def test_fuzzy_reject_low_score():
    score = compute_match_score("Payment gateway", "User login", 0.0)
    assert score < 0.78
```

## 實作注意事項
- 先以 `source_lang/target_lang` 與 `scope` 過濾候選，再進 fuzzy 計算
- CJK 可改用字元切分或 bi-gram 分詞
- 建議保留 debug 欄位（match_score、token_overlap、char_similarity）以利調參
