@echo off
chcp 65001 > nul
setlocal EnableDelayedExpansion

:: Colors
for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do (
  set "DEL=%%a"
  set "COLOR_GREEN=%%b[92m"
  set "COLOR_RED=%%b[91m"
  set "COLOR_RESET=%%b[0m"
)

echo %COLOR_GREEN%🚀 Launching Jarvis...%COLOR_RESET%

:: Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo %COLOR_RED%[!] Setup not found. Run setup_and_run.bat first.%COLOR_RESET%
    pause
    exit /b 1
)

:: Activate and Run
call venv\Scripts\activate.bat
python main.py

:: Restore CMD state
deactivate > nul 2>&1
