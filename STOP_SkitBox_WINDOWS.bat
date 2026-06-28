@echo off
setlocal
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop_dev_processes.ps1"

echo.
echo SkitBox stop check finished.
pause
