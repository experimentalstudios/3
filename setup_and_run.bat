@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ============================================
echo   Jarvis Vision - Setup and Run
echo ============================================
echo.

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo [INFO] Found Python %PYVER%

REM Check Python version is 3.11+
echo %PYVER% | findstr /R "^3\.1[1-9]" >nul
if errorlevel 1 (
    echo %PYVER% | findstr /R "^3\.[2-9][0-9]" >nul
    if errorlevel 1 (
        echo [ERROR] Python 3.11+ required. Found %PYVER%
        pause
        exit /b 1
    )
)

REM Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created.
) else (
    echo [INFO] Virtual environment already exists.
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip --quiet

REM Install requirements
echo [INFO] Installing dependencies (this may take a few minutes)...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo [SUCCESS] Dependencies installed.

echo.
echo ============================================
echo   Starting Jarvis Vision...
echo ============================================
echo.

REM Run main.py
python main.py
set EXITCODE=%errorlevel%

echo.
if %EXITCODE% neq 0 (
    echo [ERROR] Jarvis exited with code %EXITCODE%
) else (
    echo [INFO] Jarvis closed successfully.
)

pause
exit /b %EXITCODE%
