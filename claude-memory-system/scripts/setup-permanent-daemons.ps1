#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup permanent daemon auto-start on Windows
.DESCRIPTION
    Creates Windows Task Scheduler entry to start all 9 daemons on login
    Ensures daemons run permanently and restart on system reboot
#>

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "SETTING UP PERMANENT DAEMON AUTO-START" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Paths
$memoryDir = "$env:USERPROFILE\.claude\memory"
$startupScript = "$memoryDir\startup-hook.sh"
$pythonPath = (Get-Command python).Source
$bashPath = (Get-Command bash).Source

# Verify paths exist
if (!(Test-Path $memoryDir)) {
    Write-Host "[ERROR] Memory directory not found: $memoryDir" -ForegroundColor Red
    exit 1
}

if (!(Test-Path $startupScript)) {
    Write-Host "[ERROR] Startup script not found: $startupScript" -ForegroundColor Red
    exit 1
}

Write-Host "[1/4] Creating daemon startup wrapper..." -ForegroundColor Yellow

# Create PowerShell wrapper for Task Scheduler
$wrapperPath = "$memoryDir\start-all-daemons.ps1"
@"
# Auto-generated daemon startup wrapper
`$ErrorActionPreference = "SilentlyContinue"

# Change to memory directory
cd "$memoryDir"

# Start all daemons using startup-hook.sh
& "$bashPath" "$startupScript"

# Log startup
Add-Content -Path "$memoryDir\logs\daemon-startup.log" -Value "`$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Daemons started via Task Scheduler"
"@ | Out-File -FilePath $wrapperPath -Encoding UTF8

Write-Host "  [OK] Wrapper created: $wrapperPath" -ForegroundColor Green

Write-Host "[2/4] Creating Windows Task Scheduler entry..." -ForegroundColor Yellow

# Remove existing task if present
schtasks /delete /tn "ClaudeMemoryDaemons" /f 2>$null

# Create new task
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$wrapperPath`""
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable $false
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest

Register-ScheduledTask -TaskName "ClaudeMemoryDaemons" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null

Write-Host "  [OK] Task Scheduler entry created" -ForegroundColor Green

Write-Host "[3/4] Testing task execution..." -ForegroundColor Yellow

# Run task once to test
schtasks /run /tn "ClaudeMemoryDaemons"
Start-Sleep -Seconds 5

# Verify daemons started
$daemonStatus = & python "$memoryDir\daemon-manager.py" --status-all | ConvertFrom-Json
$runningCount = ($daemonStatus.PSObject.Properties | Where-Object { $_.Value.running -eq $true }).Count

if ($runningCount -ge 8) {
    Write-Host "  [OK] $runningCount/9 daemons running" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Only $runningCount/9 daemons running" -ForegroundColor Yellow
}

Write-Host "[4/4] Creating auto-restart watchdog..." -ForegroundColor Yellow

# Create watchdog script that restarts dead daemons
$watchdogPath = "$memoryDir\daemon-watchdog.ps1"
@"
# Daemon watchdog - restarts dead daemons
`$ErrorActionPreference = "SilentlyContinue"

while (`$true) {
    # Check daemon status
    `$status = & python "$memoryDir\daemon-manager.py" --status-all | ConvertFrom-Json

    # Restart any dead daemons
    foreach (`$daemon in `$status.PSObject.Properties) {
        if (`$daemon.Value.running -eq `$false) {
            Write-Host "`$(Get-Date -Format 'HH:mm:ss') - Restarting `$(`$daemon.Name)..."
            & python "$memoryDir\daemon-manager.py" --start `$daemon.Name
        }
    }

    # Check every 5 minutes
    Start-Sleep -Seconds 300
}
"@ | Out-File -FilePath $watchdogPath -Encoding UTF8

# Create watchdog Task Scheduler entry
$watchdogAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$watchdogPath`""
$watchdogTrigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$watchdogSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Days 9999)

Register-ScheduledTask -TaskName "ClaudeDaemonWatchdog" -Action $watchdogAction -Trigger $watchdogTrigger -Settings $watchdogSettings -Principal $principal -Force | Out-Null

Write-Host "  [OK] Watchdog created and scheduled" -ForegroundColor Green

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "SETUP COMPLETE!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Permanent daemon auto-start configured:" -ForegroundColor White
Write-Host "  [OK] Task: ClaudeMemoryDaemons (starts on login)" -ForegroundColor Green
Write-Host "  [OK] Task: ClaudeDaemonWatchdog (monitors & restarts)" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Daemons will auto-start on next Windows login" -ForegroundColor White
Write-Host "  2. Watchdog will auto-restart any dead daemons" -ForegroundColor White
Write-Host "  3. No manual intervention needed!" -ForegroundColor White
Write-Host ""
Write-Host "To verify:" -ForegroundColor Yellow
Write-Host "  schtasks /query /tn ClaudeMemoryDaemons" -ForegroundColor Cyan
Write-Host "  schtasks /query /tn ClaudeDaemonWatchdog" -ForegroundColor Cyan
Write-Host ""
