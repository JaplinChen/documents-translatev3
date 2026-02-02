# documents-translatev3 Full Deployment Script
# Bundled operations: Down, Build, Up, Health, Clean

Write-Host ">>> [1/5] Stopping services..." -ForegroundColor Cyan
docker compose down

Write-Host ">>> [2/5] Rebuilding and starting services..." -ForegroundColor Cyan
docker compose up -d --build

Write-Host ">>> [3/5] Verifying service status..." -ForegroundColor Cyan
docker ps

Write-Host ">>> [4/5] Running health check..." -ForegroundColor Cyan
# Using -UseBasicParsing to avoid security prompt related to Internet Explorer engine
Invoke-WebRequest -Uri "http://localhost:5002/health" -UseBasicParsing

Write-Host ">>> [5/5] Cleaning database cache..." -ForegroundColor Cyan
if (Test-Path "data/*.db") {
    Remove-Item -Path "data/*.db" -Force
    Write-Host ">>> Cache cleaned." -ForegroundColor Green
}
else {
    Write-Host ">>> No cache to clean." -ForegroundColor Yellow
}

Write-Host "`n>>> Deployment complete!" -ForegroundColor Green
