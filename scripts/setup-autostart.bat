@echo off
REM Setup Claude Insight to Auto-Start on Windows Boot

setlocal

set TASK_NAME=ClaudeInsightServer
set SCRIPT_PATH=%~dp0start-claude-insight.bat

echo.
echo ========================================
echo   Setup Auto-Start for Claude Insight
echo ========================================
echo.

REM Check if task already exists
schtasks /Query /TN "%TASK_NAME%" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [INFO] Task already exists. Deleting old task...
    schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1
)

echo [INFO] Creating scheduled task...
echo [INFO] Task Name: %TASK_NAME%
echo [INFO] Script: %SCRIPT_PATH%
echo.

REM Create scheduled task to run on startup
schtasks /Create ^
    /TN "%TASK_NAME%" ^
    /TR "\"%SCRIPT_PATH%\"" ^
    /SC ONLOGON ^
    /RL HIGHEST ^
    /F ^
    /RU "%USERNAME%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [OK] Auto-start configured successfully!
    echo.
    echo Claude Insight will now start automatically when you log in to Windows.
    echo.
    echo To disable auto-start, run: scripts\remove-autostart.bat
) else (
    echo.
    echo [ERROR] Failed to create scheduled task
    echo [ERROR] You may need to run this script as Administrator
)

echo.
pause

endlocal
