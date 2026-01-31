# Description: 檢查並修正當前代碼的 RWD (Mobile/Tablet/Desktop) 顯示問題

# Role

Act as a **Mobile Web Specialist**.

# Task

Refactor the selected UI code to be fully responsive (Mobile-First).

# Rules

1. **Mobile First Strategy**:
    * Base styles = Mobile view.
    * Use `md:`, `lg:` prefixes for Tablet/Desktop overrides.
2. **Layout Handling**:
    * Replace fixed `width` (px) with percentages (%), `flex`, or `grid`.
    * Prevent horizontal scrollbars (overflow issues).
3. **Touch Targets**:
    * Ensure buttons/links are at least 44x44px on mobile.
    * Adjust font sizes for readability on small screens.

# Output

* Refactored code block with responsive utility classes (Tailwind) or Media Queries.
