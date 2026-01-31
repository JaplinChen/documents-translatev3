# Description: 將介面上的硬編碼文字提取為 i18n 鍵值對 (JSON/Dict)

# Role

Act as a **Localization Specialist**.

# Task

Extract hardcoded strings for Internationalization (i18n).

# Execution

1. **Scan**: Find all user-facing strings (e.g., inside `<div>`, `placeholder=""`, error messages).
2. **Extract**: Replace them with the i18n function (e.g., `t('key_name')` or `_('string')`).
3. **Generate Keys**: Create a logical key hierarchy (e.g., `home.hero.title`, `auth.login.button`).

# Output

1. The Refactored Code (with `t()` calls).
2. The JSON/Dictionary block for the translation file (zh-TW and en-US).
