@echo off
chcp 65001 >nul
setlocal
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%"
for %%I in ("%~dp0..\\..") do set "CANDIDATE_ROOT=%%~fI"
if exist "%CANDIDATE_ROOT%\\frontend" (
    set "PROJECT_ROOT=%CANDIDATE_ROOT%\\"
)
cd /d "%PROJECT_ROOT%"

:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :run_script
) else (
    echo [!] Requesting Administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:run_script
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%setup.ps1"
if %errorLevel% neq 0 (
    echo.
    echo [!] PowerShell script failed with error code %errorLevel%.
    pause
)
exit /b
