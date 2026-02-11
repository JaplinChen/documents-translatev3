Write-Host "--- Ollama LAN Access Configurator ---" -ForegroundColor Cyan

# Set OLLAMA_HOST to 0.0.0.0 for the current user
[Environment]::SetEnvironmentVariable("OLLAMA_HOST", "0.0.0.0", "User")

Write-Host "SUCCESS: OLLAMA_HOST has been set to 0.0.0.0" -ForegroundColor Green
Write-Host "IMPORTANT: You MUST completely exit Ollama (Right-click icon in tray -> Exit) and restart it for changes to take effect." -ForegroundColor Yellow
Write-Host "After restarting Ollama, you can also run 'scripts/open_firewall.ps1' to open required ports." -ForegroundColor Cyan
