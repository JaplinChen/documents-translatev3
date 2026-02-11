@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ========================================
:: Configuration
:: ========================================
set "SCRIPT_DIR=%~dp0"
for %%I in ("%~dp0..\\..") do set "PROJECT_ROOT=%%~fI"
set "PROJECT_ROOT=%PROJECT_ROOT%\\"
set "BACKEND_DIR=%PROJECT_ROOT%backend"
set "FRONTEND_DIR=%PROJECT_ROOT%frontend"
set "VENV_DIR=%PROJECT_ROOT%.venv"
set "BACKEND_PORT=5005"
set "FRONTEND_PORT=5195"
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
echo   9. Start Docker (build + up)
echo.
echo   0. Exit
echo.
echo ========================================

set /p "choice=Select [0-9]: "

if "%choice%"=="1" goto START_ALL
if "%choice%"=="2" goto START_BACKEND
if "%choice%"=="3" goto START_FRONTEND
if "%choice%"=="4" goto STOP_ALL
if "%choice%"=="5" goto RESTART_ALL
if "%choice%"=="6" goto STATUS
if "%choice%"=="7" goto OPEN_BROWSER
if "%choice%"=="8" goto CHECK_OLLAMA
if "%choice%"=="9" goto START_DOCKER
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
timeout /t 8 /nobreak >nul
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

:START_DOCKER
echo.
call "%SCRIPT_DIR%start_docker.bat"
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
call :ENSURE_VENV
if errorlevel 1 goto :eof
echo [Backend] Starting...
start "Backend" /D "%PROJECT_ROOT%" cmd /k ""%VENV_DIR%\Scripts\python" -m uvicorn backend.main:app --reload --port %BACKEND_PORT% --host 0.0.0.0"
goto :eof

:DO_START_FRONTEND
call :ENSURE_NODE
if errorlevel 1 goto :eof
call :ENSURE_FRONTEND_DEPS
if errorlevel 1 goto :eof
echo [Frontend] Starting...
start "Frontend" /D "%FRONTEND_DIR%" cmd /k "npm run dev"
goto :eof

:CHECK_PORT
set "_port=%~1"
set "_name=%~2"
powershell -NoProfile -Command "if (Test-NetConnection -ComputerName 127.0.0.1 -Port %_port% -InformationLevel Quiet) { exit 0 } else { exit 1 }" >nul 2>&1
if !errorlevel! equ 0 (
    echo [OK] %_name%: Running (port %_port%)
) else (
    echo [X] %_name%: Not running
)
goto :eof

:SHOW_STATUS
call :CHECK_PORTS
goto :eof

:CHECK_PORTS
powershell -NoProfile -Command ^
"$retries = 6; $delay = 1; ^
 for ($i = 0; $i -lt $retries; $i++) { ^
   $b = Test-NetConnection -ComputerName 127.0.0.1 -Port %BACKEND_PORT% -InformationLevel Quiet -WarningAction SilentlyContinue; ^
   $f = Test-NetConnection -ComputerName 127.0.0.1 -Port %FRONTEND_PORT% -InformationLevel Quiet -WarningAction SilentlyContinue; ^
   if ($b -or $f) { break }; ^
   Start-Sleep -Seconds $delay; ^
 } ^
 if ($b) { Write-Host \"[OK] Backend: Running (port %BACKEND_PORT%)\" } else { Write-Host \"[X] Backend: Not running\" }; ^
 if ($f) { Write-Host \"[OK] Frontend: Running (port %FRONTEND_PORT%)\" } else { Write-Host \"[X] Frontend: Not running\" }"
goto :eof

:ENSURE_NODE
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Please install Node.js.
    echo [ERROR] Download: https://nodejs.org/
    exit /b 1
)
where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm not found. Please reinstall Node.js.
    exit /b 1
)
exit /b 0

:ENSURE_VENV
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [ERROR] venv python not found. Run scripts\\ops\\install.bat to recreate venv.
    exit /b 1
)
exit /b 0

:ENSURE_FRONTEND_DEPS
if not exist "%FRONTEND_DIR%\\node_modules" (
    echo [INFO] Frontend dependencies missing. Installing...
    pushd "%FRONTEND_DIR%"
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install frontend dependencies.
        popd
        exit /b 1
    )
    popd
)
if not exist "%FRONTEND_DIR%\\node_modules\\.bin\\vite.cmd" (
    echo [INFO] Frontend dependencies missing. Installing...
    pushd "%FRONTEND_DIR%"
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install frontend dependencies.
        popd
        exit /b 1
    )
    popd
)
exit /b 0
