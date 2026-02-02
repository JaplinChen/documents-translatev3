# Force UTF-8 environment for Windows PowerShell 5.1
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'

# Determine project root
$CurrentScriptDir = $PSScriptRoot
if (!$CurrentScriptDir) { $CurrentScriptDir = Split-Path $MyInvocation.MyCommand.Path -Parent }
$ProjectRoot = Get-Item (Join-Path $CurrentScriptDir "..")

# Diagnostic Log in Project Root
$LogFile = Join-Path $ProjectRoot.FullName "install_log.txt"
try {
    "--- Installation Log Start: $(Get-Date) ---" | Out-File $LogFile -Encoding utf8 -Force
}
catch {
    Write-Warning "Failed to create log file at $LogFile. Continuing without log."
}

function Write-Log($Message, $Color = "White") {
    Write-Host $Message -ForegroundColor $Color
    if (Test-Path $LogFile) {
        "$($Message)" | Out-File $LogFile -Append -Encoding utf8
    }
}

# Check for Administrator privileges
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Log "Error: Please run this script as Administrator!" "Red"
    Pause
    exit
}

# The ProjectRoot is already determined above

Write-Log "--- documents-translatev3 One-Click Installer (Diagnostic Mode) ---" "Cyan"

# 0. Check winget
Write-Log "`n[0/5] Checking winget..." "Yellow"
if (!(Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Log "Warning: winget not found. This usually happens on older Windows 10 versions. Please install 'App Installer' manually." "Red"
    Write-Log "Download Link: https://aka.ms/getwinget" "White"
    Pause
    exit
}
Write-Log "winget is ready." "Green"

# 1. Detect and install Docker Desktop
Write-Log "`n[1/5] Checking Docker Desktop..." "Yellow"
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Log "Docker not detected. Installing Docker Desktop via winget..." "Gray"
    try {
        winget install Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
        Write-Log "Docker Desktop installation complete. IMPORTANT: If this is the first time, you MUST REBOOT your computer to finalize WSL setup, then run this script again." "Green"
        Pause
        exit
    }
    catch {
        Write-Log "Error: Docker installation failed. Please download and install it manually from: https://www.docker.com/products/docker-desktop/" "Red"
        Pause
        exit
    }
}
else {
    Write-Log "Docker is already installed." "Green"
}

# Check if Docker is running
Write-Log "Waiting for Docker service to start..." "Gray"
$dockerReady = $false
for ($i = 0; $i -lt 12; $i++) {
    docker info > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        $dockerReady = $true
        break
    }
    Write-Log "Docker is not running yet. Please ensure Docker Desktop is open... ($($i+1)/12)" "Gray"
    Start-Sleep -Seconds 10
}

if (!$dockerReady) {
    Write-Log "Error: Unable to communicate with Docker. Please confirm if Docker Desktop is started and initialized." "Red"
    Pause
    exit
}

# 2. Detect and install Ollama
Write-Log "`n[2/5] Checking Ollama..." "Yellow"
if (!(Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Log "Ollama not detected. Installing via winget..." "Gray"
    winget install Ollama.Ollama --accept-package-agreements --accept-source-agreements
    Write-Log "Ollama installation complete." "Green"
}
else {
    Write-Log "Ollama is already installed." "Green"
}

# 3. Start Ollama and download model
Write-Log "`n[3/5] Configuring Ollama Model (translategemma:4b)..." "Yellow"
$retry = 0
while ($retry -lt 5) {
    try {
        $void = Invoke-RestMethod -Uri "http://localhost:11434/api/version" -ErrorAction Stop
        break
    }
    catch {
        Write-Log "Waiting for Ollama service to start... ($($retry+1)/5)" "Gray"
        Start-Process "ollama" "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 5
        $retry++
    }
}

Write-Log "Checking/Downloading translategemma:4b model..." "Gray"
ollama pull translategemma:4b
Write-Log "Model is ready." "Green"

# 4. Load and start Docker project
Write-Log "`n[4/5] Starting documents-translatev3 system..." "Yellow"

# Load local images
$BackendTar = Join-Path $ProjectRoot.FullName "backend_image.tar"
$FrontendTar = Join-Path $ProjectRoot.FullName "frontend_image.tar"

if (Test-Path $BackendTar) {
    Write-Log "Loading Backend Image (this may take 1-2 mins)..." "Gray"
    docker load -i $BackendTar
}
if (Test-Path $FrontendTar) {
    Write-Log "Loading Frontend Image..." "Gray"
    docker load -i $FrontendTar
}

# Ensure backend/.env exists to prevent mount failure
$EnvFile = Join-Path $ProjectRoot.FullName "backend\.env"
if (!(Test-Path (Join-Path $ProjectRoot.FullName "backend"))) {
    New-Item -ItemType Directory -Path (Join-Path $ProjectRoot.FullName "backend") -ErrorAction SilentlyContinue | Out-Null
}
if (!(Test-Path $EnvFile)) {
    New-Item -ItemType File -Path $EnvFile -Force | Out-Null
}

Set-Location $ProjectRoot.FullName
Write-Log "Starting container services..." "Gray"
docker compose up -d

Write-Log "`n[5/5] Confirming service status..." "Yellow"
docker ps --format "table {{.Names}}\t{{.Status}}"

Write-Log "`n===============================================" "Cyan"
Write-Log "Setup and startup completed!" "Green"
Write-Log "Frontend URL: http://localhost:5194" "White"
Write-Log "Backend URL: http://localhost:5002" "White"
Write-Log "===============================================" "Cyan"
Write-Log "Log saved to: $LogFile" "Gray"
Pause
