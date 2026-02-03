from backend.services.tm_matcher import compute_match_score, fuzzy_match


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


def test_fuzzy_match_limit_and_scope():
    candidates = [
        {"source_text": "User profile update", "domain": "auth", "category": "account", "scope_type": "project", "scope_id": "p1"},
        {"source_text": "Update profile", "domain": "auth", "category": "account", "scope_type": "project", "scope_id": "p1"},
        {"source_text": "Profile update", "domain": "auth", "category": "account", "scope_type": "project", "scope_id": "p1"},
        {"source_text": "Profile change", "domain": "auth", "category": "account", "scope_type": "project", "scope_id": "p1"},
    ]
    scope = {"domain": "auth", "category": "account", "scope_type": "project", "scope_id": "p1"}
    results = fuzzy_match("User profile update", candidates, scope, min_score=0.78, limit=3)
    assert len(results) == 3
