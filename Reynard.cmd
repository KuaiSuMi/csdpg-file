@echo off
setlocal
chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"
python -u "%~dp0scripts\run_baseline.py" reynard
set "baselineExit=%errorlevel%"
if /i not "%~1"=="--no-pause" pause
exit /b %baselineExit%
