# Description: 逆向分析現有代碼，產出可執行的技術規格書 (PRD)

# Role

Act as a **Solution Architect** & **Technical Writer**.

# Task

Reverse engineer the current file/project structure into a "Technical Requirement Document (PRD)".

# Analysis Scope

1. **Architecture**: Tech stack, Patterns (MVC/Flux), Dependencies.
2. **Logic & Data**: Core business logic, User flows, Data Schema (Fields/Constraints).
3. **UI/UX**: Design tokens (Colors, Fonts), Component styles.

# Output Format (Markdown)

Produce a `TECH_SPEC.md` containing:

1. ## Core Architecture

2. ## Functional Matrix & User Flows

3. ## Data Schema (Strict Definition)

4. ## UI/UX Design Tokens

5. ## Technical Logic (Pseudocode)

# Constraint

* The doc must be "Executable": A developer must be able to rebuild the app solely from this doc.
* Use professional technical terminology.
