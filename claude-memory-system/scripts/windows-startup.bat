@echo off
REM ========================================
REM Claude Memory System - Windows Startup
REM ========================================
REM
REM This script automatically starts all automation daemons
REM when Windows boots or user logs in.
REM
REM Location: %USERPROFILE%\.claude\memory\windows-startup.bat
REM ========================================

echo.
echo ========================================
echo Claude Memory System Startup
echo ========================================
echo.

REM Change to memory directory
cd /d "%USERPROFILE%\.claude\memory"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python or add to PATH
    pause
    exit /b 1
)

echo [1/3] Checking existing daemons...

REM Stop any existing daemons first (clean start)
python daemon-manager.py --stop-all >nul 2>&1

echo [2/3] Starting all automation daemons...

REM Start all daemons
python daemon-manager.py --start-all

echo [3/3] Verifying daemon status...

REM Wait 3 seconds for daemons to initialize
timeout /t 3 /nobreak >nul

REM Check status
python daemon-manager.py --status-all

echo.
echo ========================================
echo Claude Memory System Started
echo ========================================
echo.
echo All automation daemons are now running!
echo.
echo You can close this window or press any key...
pause >nul

exit /b 0
