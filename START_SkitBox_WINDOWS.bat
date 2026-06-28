@echo off
setlocal
cd /d "%~dp0"

if not defined SKITBOX_HOME (
  set "SKITBOX_HOME=%~dp0user_data"
  if exist "D:\" (
    if not exist "D:\SkitBoxData" mkdir "D:\SkitBoxData" 2>nul
    if exist "D:\SkitBoxData" set "SKITBOX_HOME=D:\SkitBoxData"
  )
)

if not defined TEMP set "TEMP=%SKITBOX_HOME%\temp"
if not defined TMP set "TMP=%TEMP%"

if exist "D:\" (
  if not exist "D:\Temp" mkdir "D:\Temp" 2>nul
  if exist "D:\Temp" (
    set "TEMP=D:\Temp"
    set "TMP=D:\Temp"
  )
)

if not exist "%SKITBOX_HOME%" mkdir "%SKITBOX_HOME%" 2>nul
if not exist "%TEMP%" mkdir "%TEMP%" 2>nul

set "PYTHON_CMD="
call :check_python python
if defined PYTHON_CMD goto run_app
call :check_python py -3
if defined PYTHON_CMD goto run_app

echo SkitBox needs Python 3.10 or newer.
echo.
echo What to do:
echo   1. Go to https://www.python.org/downloads/windows/
echo   2. Download and install Python.
echo   3. Tick "Add python.exe to PATH" during install.
echo   4. Double-click START_SkitBox_WINDOWS.bat again.
echo.
echo SkitBox has not changed your system.
echo.
pause
exit /b 1

:run_app
echo Starting SkitBox with %PYTHON_CMD% ...
echo Data folder: %SKITBOX_HOME%
echo Temp folder: %TEMP%
echo Your browser should open in a moment.
echo.
%PYTHON_CMD% -m sitcom_engine_app.app
pause
exit /b 0

:check_python
%* -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=%*"
exit /b 0
