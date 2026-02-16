# ========================================
# Claude Memory System - Setup Windows Startup
# ========================================
#
# This PowerShell script registers the Claude Memory System
# to automatically start on Windows login
#
# Usage:
#   Run as Administrator:
#   powershell -ExecutionPolicy Bypass -File setup-windows-startup.ps1
#
# ========================================

Write-Host ""
Write-Host "========================================"
Write-Host "Claude Memory System - Startup Setup"
Write-Host "========================================"
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "WARNING: Not running as Administrator" -ForegroundColor Yellow
    Write-Host "Some features may not work. Run PowerShell as Administrator for best results." -ForegroundColor Yellow
    Write-Host ""
}

# Paths
$memoryDir = "$env:USERPROFILE\.claude\memory"
$vbsScript = "$memoryDir\windows-startup-silent.vbs"
$taskName = "ClaudeMemorySystemStartup"

# Verify files exist
if (-not (Test-Path $vbsScript)) {
    Write-Host "ERROR: Startup script not found at: $vbsScript" -ForegroundColor Red
    exit 1
}

Write-Host "[1/4] Creating scheduled task..." -ForegroundColor Green

# Create task action (run VBS script)
$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$vbsScript`""

# Create trigger (at logon)
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

# Create settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Create principal (run as current user)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Write-Host "[2/4] Registering task with Windows Task Scheduler..." -ForegroundColor Green

try {
    # Check if task already exists
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

    if ($existingTask) {
        Write-Host "   Task already exists. Updating..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }

    # Register new task
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Automatically starts Claude Memory System daemons on login" | Out-Null

    Write-Host "   SUCCESS: Task registered successfully!" -ForegroundColor Green

} catch {
    Write-Host "   ERROR: Failed to register task: $_" -ForegroundColor Red
    exit 1
}

Write-Host "[3/4] Verifying task..." -ForegroundColor Green

$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($task) {
    Write-Host "   Task Name: $taskName" -ForegroundColor Cyan
    Write-Host "   State: $($task.State)" -ForegroundColor Cyan
    Write-Host "   Trigger: At user logon ($env:USERNAME)" -ForegroundColor Cyan
    Write-Host "   Action: Run $vbsScript" -ForegroundColor Cyan
} else {
    Write-Host "   WARNING: Task not found after registration" -ForegroundColor Yellow
}

Write-Host "[4/4] Testing startup (starting daemons now)..." -ForegroundColor Green

# Run the startup script now to test
Start-Process -FilePath "wscript.exe" -ArgumentList "`"$vbsScript`"" -Wait

# Wait for daemons to start
Start-Sleep -Seconds 5

# Check daemon status
Write-Host ""
Write-Host "Checking daemon status..." -ForegroundColor Green
python "$memoryDir\daemon-manager.py" --status-all

Write-Host ""
Write-Host "========================================"
Write-Host "Setup Complete!"
Write-Host "========================================"
Write-Host ""
Write-Host "What happens now:" -ForegroundColor Green
Write-Host "  - All daemons are running RIGHT NOW" -ForegroundColor Cyan
Write-Host "  - On next Windows login, daemons will auto-start" -ForegroundColor Cyan
Write-Host "  - No manual intervention needed" -ForegroundColor Cyan
Write-Host "  - Task runs silently in background" -ForegroundColor Cyan
Write-Host ""
Write-Host "To verify:" -ForegroundColor Yellow
Write-Host "  1. Open Task Scheduler (taskschd.msc)" -ForegroundColor White
Write-Host "  2. Look for task: '$taskName'" -ForegroundColor White
Write-Host "  3. Right-click -> Run to test" -ForegroundColor White
Write-Host ""
Write-Host "To disable:" -ForegroundColor Yellow
Write-Host "  Open Task Scheduler and disable/delete '$taskName'" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to exit"
