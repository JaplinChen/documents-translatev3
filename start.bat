@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ========================================
REM Documents Translate - 啟動腳本
REM ========================================

set "PROJECT_ROOT=%~dp0"
set "BACKEND_DIR=%PROJECT_ROOT%backend"
set "FRONTEND_DIR=%PROJECT_ROOT%frontend"
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=5193"

set "BACKEND_PID="
set "FRONTEND_PID="

:MAIN_MENU
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║          Documents Translate - 啟動選單                      ║
echo ╠════════════════════════════════════════════════════════════╣
echo ║  1. 啟動前後端 (預設)                                        ║
echo ║  2. 僅啟動後端 (Backend)                                    ║
echo ║  3. 僅啟動前端 (Frontend)                                   ║
echo ║  4. 停止所有服務                                            ║
echo ║  5. 重啟所有服務                                            ║
echo ║  6. 查看服務狀態                                            ║
echo ║  7. 開啟測試頁面                                            ║
echo ║                                                            ║
echo ║  0. 離開                                                    ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

set /p "choice=請選擇 [0-7]: "

if "%choice%"=="1" goto START_ALL
if "%choice%"=="2" goto START_BACKEND
if "%choice%"=="3" goto START_FRONTEND
if "%choice%"=="4" goto STOP_ALL
if "%choice%"=="5" goto RESTART_ALL
if "%choice%"=="6" goto STATUS
if "%choice%"=="7" goto OPEN_TEST
if "%choice%"=="0" goto EXIT

echo 無效選擇，請重新輸入
pause
goto MAIN_MENU

:START_ALL
echo.
echo 正在啟動後端服務...
start "Backend - Documents Translate" cmd /c "cd /d "%BACKEND_DIR%" && uvicorn backend.main:app --reload --port %BACKEND_PORT%"
set BACKEND_LAUNCHED=1

echo 正在啟動前端服務...
start "Frontend - Documents Translate" cmd /c "cd /d "%FRONTEND_DIR%" && npm run dev"
set FRONTEND_LAUNCHED=1

echo.
if defined BACKEND_LAUNCHED echo ✓ 後端已啟動 (http://localhost:%BACKEND_PORT%)
if defined FRONTEND_LAUNCHED echo ✓ 前端已啟動 (http://localhost:%FRONTEND_PORT%)
echo.
echo 3 秒後開啟瀏覽器...
timeout /t 3 /nobreak >nul
start http://localhost:%FRONTEND_PORT%
goto END

:START_BACKEND
echo.
echo 正在啟動後端服務...
start "Backend - Documents Translate" cmd /c "cd /d "%BACKEND_DIR%" && uvicorn backend.main:app --reload --port %BACKEND_PORT%"
echo.
echo ✓ 後端已啟動 (http://localhost:%BACKEND_PORT%)
echo.
pause
goto END

:START_FRONTEND
echo.
echo 正在啟動前端服務...
start "Frontend - Documents Translate" cmd /c "cd /d "%FRONTEND_DIR%" && npm run dev"
echo.
echo ✓ 前端已啟動 (http://localhost:%FRONTEND_PORT%)
echo 3 秒後開啟瀏覽器...
timeout /t 3 /nobreak >nul
start http://localhost:%FRONTEND_PORT%
pause
goto END

:STOP_ALL
echo.
echo 正在停止服務...

REM 停止後端
taskkill /FI "WINDOWTITLE eq Backend*" /IM cmd.exe /F >nul 2>&1
if !errorlevel! equ 0 (
    echo ✓ 後端已停止
) else (
    echo 後端未運行
)

REM 停止前端
taskkill /FI "WINDOWTITLE eq Frontend*" /IM cmd.exe /F >nul 2>&1
if !errorlevel! equ 0 (
    echo ✓ 前端已停止
) else (
    echo 前端未運行
)

REM 額外清理
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1

echo.
pause
goto END

:RESTART_ALL
echo.
echo 正在重啟服務...
call :STOP_ALL
echo.
echo 3 秒後啟動服務...
timeout /t 3 /nobreak >nul
goto START_ALL

:STATUS
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                    服務狀態                                  ║
echo ╠════════════════════════════════════════════════════════════╣

REM 檢查後端
netstat -an | find ":%BACKEND_PORT%" >nul 2>&1
if !errorlevel! equ 0 (
    echo ║  後端:   ✓ 運行中 (port %BACKEND_PORT%)                      ║
) else (
    echo ║  後端:   ✗ 未運行 (port %BACKEND_PORT%)                      ║
)

REM 檢查前端
netstat -an | find ":%FRONTEND_PORT%" >nul 2>&1
if !errorlevel! equ 0 (
    echo ║  前端:   ✓ 運行中 (port %FRONTEND_PORT%)                      ║
) else (
    echo ║  前端:   ✗ 未運行 (port %FRONTEND_PORT%)                      ║
)

echo ╚════════════════════════════════════════════════════════════╝
echo.
echo API 文件: http://localhost:%BACKEND_PORT%/docs
echo 前端頁面: http://localhost:%FRONTEND_PORT%
echo.
pause
goto END

:OPEN_TEST
start http://localhost:%FRONTEND_PORT%
echo 已開啟瀏覽器
goto END

:EXIT
exit /b 0

:END
endlocal
