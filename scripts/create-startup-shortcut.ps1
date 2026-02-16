# Create Startup Shortcut for Claude Insight

$StartupFolder = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
$ShortcutPath = "$StartupFolder\Claude Insight Server.lnk"
$TargetPath = "$PSScriptRoot\start-claude-insight.bat"
$WorkingDir = Split-Path $PSScriptRoot

Write-Host ""
Write-Host "Creating startup shortcut..."
Write-Host "Target: $TargetPath"
Write-Host "Location: $ShortcutPath"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetPath
$Shortcut.WorkingDirectory = $WorkingDir
$Shortcut.WindowStyle = 7  # Minimized
$Shortcut.Description = "Start Claude Insight Server on Login"
$Shortcut.Save()

Write-Host ""
Write-Host "[OK] Shortcut created successfully!"
Write-Host "[OK] Claude Insight will start on next login"
Write-Host ""
