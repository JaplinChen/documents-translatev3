\
$ErrorActionPreference = "Stop"
pwsh -NoProfile -ExecutionPolicy Bypass -File verify-frontend.ps1
pwsh -NoProfile -ExecutionPolicy Bypass -File verify-backend.ps1
