@echo off
REM Add Claude Insight to Windows Startup Folder (No Admin Required)

setlocal

set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SHORTCUT_NAME=Claude Insight Server.lnk
set TARGET_SCRIPT=%~dp0start-claude-insight.bat

echo.
echo ========================================
echo   Add Claude Insight to Startup Folder
echo ========================================
echo.
echo Startup Folder: %STARTUP_FOLDER%
echo Target Script: %TARGET_SCRIPT%
echo.

REM Create shortcut using PowerShell
powershell -Command ^
"$WshShell = New-Object -ComObject WScript.Shell; ^
$Shortcut = $WshShell.CreateShortcut('%STARTUP_FOLDER%\%SHORTCUT_NAME%'); ^
$Shortcut.TargetPath = '%TARGET_SCRIPT%'; ^
$Shortcut.WorkingDirectory = '%~dp0..'; ^
$Shortcut.WindowStyle = 7; ^
$Shortcut.Description = 'Start Claude Insight Server on Login'; ^
$Shortcut.Save()"

if %ERRORLEVEL% EQU 0 (
    echo [OK] Shortcut created successfully!
    echo [OK] Location: %STARTUP_FOLDER%\%SHORTCUT_NAME%
    echo.
    echo Claude Insight will start automatically on next login!
) else (
    echo [ERROR] Failed to create shortcut
)

echo.
pause

endlocal
