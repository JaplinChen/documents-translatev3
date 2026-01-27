import re

def _is_technical_terms_only(text: str) -> bool:
    """
    Check if the text consists only of technical terms, product names,
    or acronyms.

    Examples that should return True:
    - "Notion"
    - "Obsidian"
    - "Wiki, SOP, CRM"
    - "Tao wiki, SOP, database, tracker, automation"
    - "API"
    - "REST, GraphQL, gRPC"

    Examples that should return False:
    - "This is a sentence with Notion"
    - "使用 SOP 進行管理"
    - "Please configure the API settings"
    """
    if not text.strip():
        return True

    # Remove common separators
    cleaned = re.sub(r"[,、，/\s]+", " ", text).strip()

    # If contains CJK characters, it's not pure technical terms.
    if re.search(r"[\u4e00-\u9fff\u3040-\u30ff\u0e00-\u0e7f]", cleaned):
        return False

    # Check if contains sentence-forming words (articles, prepositions, verbs)
    sentence_indicators = (
        r"\b(the|a|an|is|are|was|were|be|have|has|had|do|does|did|"
        r"will|would|can|could|should|may|might|must|please|this|"
        r"that|these|those|with|from|to|in|on|at|for|of|and|or|but)\b"
    )
    if re.search(sentence_indicators, cleaned, re.IGNORECASE):
        return False

    # Split into words
    words = cleaned.split()

    # If only contains technical-looking words (not full sentences)
    # Allow up to 10 words to accommodate term lists
    if len(words) <= 10:
        # Check if all words are either:
        # 1. All uppercase (acronyms like SOP, CRM)
        # 2. Title case (product names like Notion, Obsidian)
        # 3. lowercase technical terms (wiki, database, tracker)
        # 4. Mixed case technical names (GraphQL, iOS, macOS)
        technical_pattern = (
            r"^[A-Z][a-z]*$|^[A-Z]+$|^[a-z]+$|"
            r"^[A-Z][a-z]*[A-Z][a-zA-Z]*$"
        )
        if all(re.match(technical_pattern, word) for word in words):
            return True

    return False


# Test cases
test_cases = [
    ("Notion", True),
    ("Obsidian", True),
    ("Wiki, SOP, CRM", True),
    ("Tao wiki, SOP, database, tracker, automation", True),
    ("API", True),
    ("REST, GraphQL, gRPC", True),
    ("wiki", True),
    ("database", True),
    ("This is a sentence with Notion", False),
    ("使用 SOP 進行管理", False),
    ("Please configure the API settings", False),
    ("The system uses REST API", False),
    ("Configure the database", False),
    ("內容", False),
    ("NỘI DUNG 內容", False),
    ("123", False),  # This should be caught by numeric_only instead
]

print("Testing _is_technical_terms_only:")
for text, expected in test_cases:
    result = _is_technical_terms_only(text)
    status = "✓" if result == expected else "✗"
    print(f"{status} '{text}' -> {result} (expected: {expected})")
