@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ========================================
:: Configuration
:: ========================================
set "PROJECT_ROOT=%~dp0"
set "BACKEND_DIR=%PROJECT_ROOT%backend"
set "FRONTEND_DIR=%PROJECT_ROOT%frontend"
set "VENV_DIR=%PROJECT_ROOT%.venv"
set "BACKEND_PORT=5001"
set "FRONTEND_PORT=5193"
set "OLLAMA_URL=http://127.0.0.1:11434"

:: ========================================
:: Environment Setup
:: ========================================
if not exist "%VENV_DIR%" (
    echo [INFO] Creating virtual environment...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create venv. Please install Python.
        pause
        exit /b 1
    )
    echo [INFO] Installing dependencies...
    "%VENV_DIR%\Scripts\pip" install -r "%PROJECT_ROOT%requirements.txt"
)

:MAIN_MENU
cls
echo.
echo ========================================
echo    Documents Translate - Startup Menu
echo ========================================
echo.
echo   1. Start Backend + Frontend
echo   2. Backend only (port %BACKEND_PORT%)
echo   3. Frontend only (port %FRONTEND_PORT%)
echo   4. Stop all services
echo   5. Restart all
echo   6. Check status
echo   7. Open browser
echo   8. Check Ollama
echo.
echo   0. Exit
echo.
echo ========================================

set /p "choice=Select [0-8]: "

if "%choice%"=="1" goto START_ALL
if "%choice%"=="2" goto START_BACKEND
if "%choice%"=="3" goto START_FRONTEND
if "%choice%"=="4" goto STOP_ALL
if "%choice%"=="5" goto RESTART_ALL
if "%choice%"=="6" goto STATUS
if "%choice%"=="7" goto OPEN_BROWSER
if "%choice%"=="8" goto CHECK_OLLAMA
if "%choice%"=="0" goto EXIT

echo Invalid choice
pause
goto MAIN_MENU

:: ========================================
:: Service Control
:: ========================================
:START_ALL
echo.
call :DO_START_BACKEND
call :DO_START_FRONTEND
echo.
echo Waiting for services...
timeout /t 5 /nobreak >nul
call :SHOW_STATUS
start http://localhost:%FRONTEND_PORT%
echo Browser opened...
pause
goto MAIN_MENU

:START_BACKEND
echo.
call :DO_START_BACKEND
timeout /t 3 /nobreak >nul
call :CHECK_PORT %BACKEND_PORT% "Backend"
pause
goto MAIN_MENU

:START_FRONTEND
echo.
call :DO_START_FRONTEND
timeout /t 3 /nobreak >nul
call :CHECK_PORT %FRONTEND_PORT% "Frontend"
start http://localhost:%FRONTEND_PORT%
pause
goto MAIN_MENU

:STOP_ALL
echo.
echo Stopping services...
taskkill /F /IM uvicorn.exe >nul 2>&1
echo [OK] Backend stopped
taskkill /F /IM node.exe >nul 2>&1
echo [OK] Frontend stopped
pause
goto MAIN_MENU

:RESTART_ALL
echo.
echo Restarting...
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 /nobreak >nul
goto START_ALL

:STATUS
cls
echo.
echo ========================================
echo              Service Status
echo ========================================
call :SHOW_STATUS
echo.
echo ========================================
echo API Docs: http://localhost:%BACKEND_PORT%/docs
echo Frontend: http://localhost:%FRONTEND_PORT%
echo ========================================
pause
goto MAIN_MENU

:OPEN_BROWSER
start http://localhost:%FRONTEND_PORT%
goto MAIN_MENU

:CHECK_OLLAMA
cls
echo.
echo ========================================
echo           Ollama Health Check
echo ========================================
echo.
echo Checking connection to %OLLAMA_URL%...
echo.
curl -s -o nul -w "HTTP Status: %%{http_code}" "%OLLAMA_URL%"
if errorlevel 1 (
    echo.
    echo [ERROR] Cannot connect to Ollama at %OLLAMA_URL%
    echo.
    echo Possible solutions:
    echo   1. Ensure Ollama is running: ollama serve
    echo   2. Check if Ollama listens on the correct IP
    echo   3. Verify firewall settings
) else (
    echo.
    echo [OK] Ollama is running!
)
echo.
pause
goto MAIN_MENU

:EXIT
exit /b 0

:: ========================================
:: Helper Functions
:: ========================================
:DO_START_BACKEND
echo [Backend] Starting...
start "Backend" cmd /c "cd /d "%BACKEND_DIR%" && "%VENV_DIR%\Scripts\python" -m uvicorn backend.main:app --reload --port %BACKEND_PORT% --host 0.0.0.0"
goto :eof

:DO_START_FRONTEND
echo [Frontend] Starting...
start "Frontend" cmd /c "cd /d "%FRONTEND_DIR%" && npm run dev"
goto :eof

:CHECK_PORT
set "_port=%~1"
set "_name=%~2"
netstat -an | find ":%_port%" >nul 2>&1
if !errorlevel! equ 0 (
    echo [OK] %_name%: Running (port %_port%)
) else (
    echo [X] %_name%: Not running
)
goto :eof

:SHOW_STATUS
call :CHECK_PORT %BACKEND_PORT% "Backend"
call :CHECK_PORT %FRONTEND_PORT% "Frontend"
goto :eof
