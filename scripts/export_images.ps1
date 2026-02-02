# Force UTF-8 encoding environment
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'

$ProjectRoot = Get-Item $PSScriptRoot\..
Set-Location $ProjectRoot.FullName

Write-Host "--- documents-translatev3 Image Export Tool (Source Code Protection) ---" -ForegroundColor Cyan

# 1. Create export directory
$ExportDir = Join-Path $ProjectRoot.FullName "release_package"
if (!(Test-Path $ExportDir)) {
  New-Item -ItemType Directory -Path $ExportDir
}

# 2. Build images
Write-Host "[1/3] Building Docker Images (this may take some time)..." -ForegroundColor Yellow
docker compose build

# 3. Export images to .tar files
Write-Host "[2/3] Exporting images to .tar files..." -ForegroundColor Yellow

Write-Host "Exporting Backend Image (documents-translatev3-backend)..." -ForegroundColor Gray
docker save documents-translatev3-backend:latest -o (Join-Path $ExportDir "backend_image.tar")

Write-Host "Exporting Frontend Image (documents-translatev3-frontend)..." -ForegroundColor Gray
docker save documents-translatev3-frontend:latest -o (Join-Path $ExportDir "frontend_image.tar")

# 4. Copy necessary config files (NO source code)
Write-Host "[3/3] Preparing release package content..." -ForegroundColor Yellow

# Copy docker-compose.release.yml (modified to use image instead of build)
$ComposeRelease = @"
services:
  backend:
    image: documents-translatev3-backend:latest
    container_name: documents-translatev3-backend
    ports:
      - "5005:5005"
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      - LLM_PROVIDER=\${LLM_PROVIDER:-ollama}
      - TRANSLATE_LLM_MODE=\${TRANSLATE_LLM_MODE:-real}
      - OLLAMA_BASE_URL=\${OLLAMA_BASE_URL:-http://host.docker.internal:11434}
      - OLLAMA_MODEL=\${OLLAMA_MODEL:-translategemma:4b}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: [ "CMD", "curl", "-f", "http://localhost:5005/health" ]
      interval: 30s
      timeout: 10s
      retries: 5

  frontend:
    image: documents-translatev3-frontend:latest
    container_name: documents-translatev3-frontend
    ports:
      - "5195:80"
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped

networks:
  default:
    name: documents-translatev3-network
"@
$ComposeRelease | Out-File -FilePath (Join-Path $ExportDir "docker-compose.yml") -Encoding utf8

# Copy install scripts
Copy-Item (Join-Path $ProjectRoot.FullName "install.bat") (Join-Path $ExportDir "install.bat")
if (!(Test-Path (Join-Path $ExportDir "scripts"))) { New-Item -ItemType Directory -Path (Join-Path $ExportDir "scripts") }
Copy-Item (Join-Path $ProjectRoot.FullName "scripts\setup.ps1") (Join-Path $ExportDir "scripts\setup.ps1")

Write-Host "`nPacking complete! Please compress the 'release_package' folder and distribute it." -ForegroundColor Green
Write-Host "This directory currently contains NO source code folders." -ForegroundColor White
