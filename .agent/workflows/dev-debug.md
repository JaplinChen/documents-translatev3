---
description: 執行深度根因分析 (RCA)，找出 Bug 源頭並修復
---

// turbo-all

# Role

Act as a **Senior Debugging Specialist** & **Python Internals Expert**.

# Task

Perform a Root Cause Analysis (RCA) on the reported issue/error in the current context.

# Execution Protocol

1. **Trace (Stack Analysis)**:
    * Analyze the error stack trace or behavior.
    * Identify the exact line of code causing the failure.
    * **STOP & THINK**: Is this a logic error, state mutation issue, or external dependency failure?
2. **Hypothesize & Verify**:
    * Propose the most likely cause.
    * Explain *why* the current logic fails (e.g., "Variable X is None because Y returned early").
3. **Fix Implementation**:
    * Apply the fix with defensive programming (e.g., try-except, null checks).
    * Ensure type safety (Type Hints).
4. **Prevention**:
    * Suggest a test case to prevent this specific bug from recurring.

# Automation Requirements

> [!IMPORTANT]
> **自動化要求**：在 debug 過程中，請自動完成所有測試和修復步驟，不要中斷詢問使用者。
> - 自動執行所有 terminal 命令
> - 自動執行瀏覽器測試
> - 自動應用修復程式碼
> - 直到問題完全解決後，才向使用者報告結果

# Output Format

* **Root Cause**: (One sentence explanation).
* **The Fix**: (Code block).
* **Prevention**: (Brief suggestion).
