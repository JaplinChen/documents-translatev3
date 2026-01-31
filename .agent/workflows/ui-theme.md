# Description: 將寫死的顏色/數值 (Hardcoded Values) 替換為專案的設計變數

# Role

Act as a **Design System Maintainer**.

# Task

Scan the code for "Magic Numbers" and "Hardcoded Colors", replacing them with Design Tokens.

# Execution

1. **Analyze**: Look for hex codes (`#F00`), pixels (`16px`), or raw values.
2. **Map**: Compare against `tailwind.config.js` or `global.css` variables.
    * Example: `#EF4444` -> `text-red-500` or `var(--color-error)`.
    * Example: `padding: 20px` -> `p-5` or `var(--spacing-xl)`.
3. **Refactor**: Apply the standardized variables.

# Output

* Only the modified lines/blocks.
* List any values that *could not* be mapped to the theme (potential inconsistencies).
