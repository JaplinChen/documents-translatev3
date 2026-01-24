@echo off
setlocal
set REPO=%~dp0
powershell -NoProfile -ExecutionPolicy Bypass -File "%REPO%watch_update.ps1" -RepoPath "%REPO%"
