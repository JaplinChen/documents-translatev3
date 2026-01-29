@echo off
setlocal

echo ========================================
echo   Documents Translate - Docker Startup
echo ========================================
echo.

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

echo [1/3] Stopping existing containers...
docker compose down >nul 2>&1

echo [2/3] 建置並啟動容器...
docker compose up -d --build
if errorlevel 1 (
    echo [ERROR] Failed to start containers.
    pause
    exit /b 1
)

echo [3/3] Waiting for services...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo  Access URLs
echo ========================================
echo  Frontend: http://localhost:5194
echo  Backend:  http://localhost:5002
echo  API Docs: http://localhost:5002/docs
echo ========================================
echo.

pause
