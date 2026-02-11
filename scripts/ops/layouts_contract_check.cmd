@echo off
setlocal
cd /d "%~dp0\..\.."
python scripts\dev\run_layouts_contract_check.py --full-tests --frontend-build

