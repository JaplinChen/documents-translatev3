# Description: 針對「已經寫好但沒有測試」的代碼，補充單元測試以提高覆蓋率

# Role

Act as a **QA Automation Engineer**.

# Task

Write comprehensive Unit Tests for the selected existing code.

# Strategy

1. **Happy Path**: Write a test case for the successful execution scenario.
2. **Edge Cases**: Test specifically for:
    * Null/None inputs.
    * Empty lists/strings.
    * Boundary values (0, negative numbers).
3. **Mocking**:
    * If the code calls DB or External API, use `unittest.mock` or `pytest-mock`.
    * NEVER make real network calls in unit tests.

# Output

* Complete test file using `pytest`.
