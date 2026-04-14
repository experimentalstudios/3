@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ============================================
echo   Jarvis Vision - Uninstall
echo ============================================
echo.

REM Prompt for confirmation
set /p CONFIRM="This will remove all local AI data (venv/ and models/). Continue? (Y/N): "

if /i not "%CONFIRM%"=="Y" (
    echo [INFO] Uninstall cancelled.
    pause
    exit /b 0
)

echo.
echo [INFO] Starting uninstallation...
echo.

REM Kill any running Python processes matching this project
echo [INFO] Stopping running Jarvis processes...
taskkill /F /FI "WINDOWTITLE eq Jarvis*" >nul 2>&1
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *jarvis*" >nul 2>&1
timeout /t 2 /nobreak >nul

REM Delete virtual environment
if exist "venv\" (
    echo [INFO] Removing virtual environment...
    rmdir /s /q "venv"
    if errorlevel 1 (
        echo [WARNING] Could not delete venv\ folder. It may be in use.
    ) else (
        echo [SUCCESS] Removed venv\ folder.
    )
) else (
    echo [INFO] venv\ folder not found. Skipping.
)

REM Delete models directory
if exist "models\" (
    echo [INFO] Removing AI models (this may take a while)...
    rmdir /s /q "models"
    if errorlevel 1 (
        echo [WARNING] Could not delete models\ folder. Some files may be in use.
    ) else (
        echo [SUCCESS] Removed models\ folder.
    )
) else (
    echo [INFO] models\ folder not found. Skipping.
)

REM Delete log files
if exist "jarvis.log" (
    del /q "jarvis.log"
    echo [SUCCESS] Removed jarvis.log
)

REM Delete __pycache__ folders
if exist "__pycache__" (
    rmdir /s /q "__pycache__"
    echo [SUCCESS] Removed __pycache__
)

echo.
echo ============================================
echo   Uninstall Complete
echo ============================================
echo.
echo All local AI data has been removed.
echo To reinstall, run setup_and_run.bat again.
echo.

pause
exit /b 0
