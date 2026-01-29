@echo off
setlocal

where docker >nul 2>&1
if errorlevel 1 (
  echo [ERROR] docker not found. Please install Docker Desktop.
  pause
  exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Docker is not running. Please start Docker Desktop.
  pause
  exit /b 1
)

if not exist ".env" (
  echo [WARNING] .env not found. Creating from .env.example...
  copy ".env.example" ".env" >nul
)

echo [1/2] Starting containers...
docker compose up -d backend frontend
if errorlevel 1 (
  echo [ERROR] Failed to start containers.
  pause
  exit /b 1
)

echo [2/2] Watching for changes...
 echo   - frontend/src  -> rebuild frontend
 echo   - frontend/public -> rebuild frontend
 echo   - backend -> sync/reload
 echo   (Press Ctrl+C to stop)

:: foreground watch (requires Docker Compose v2.22+)
docker compose watch

pause
