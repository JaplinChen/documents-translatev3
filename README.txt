Windows-native package (no bash required on Windows)

Install prerequisites:
- Node.js + npm
- Codex CLI: npm i -g @openai/codex
- Python 3
- PowerShell 7 (pwsh) recommended (Windows 11 usually has it; otherwise install)

Backend deps:
- uv preferred (https://astral.sh/uv) or poetry

Usage:
- Put these files in repo root (keeping paths)
- VS Code: Run Task -> "AI: Route + Fix (Web+Python, zoned, Windows native)"
- The router will:
  1) Decide zone and tier
  2) Invoke Codex CLI with selected model/effort/approval
  3) Run verification via verify-*.ps1 on Windows, verify-*.sh on Unix
