#!/usr/bin/env pwsh
# Daemon Watchdog - Auto-restart dead daemons
# Runs every 5 minutes and checks daemon health

$ErrorActionPreference = "SilentlyContinue"

$memoryDir = "$env:USERPROFILE\.claude\memory"
$logFile = "$memoryDir\logs\daemon-watchdog.log"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $logFile -Value "[$timestamp] $Message"
}

Write-Log "Watchdog started"

while ($true) {
    try {
        # Check daemon status
        $statusJson = & python "$memoryDir\daemon-manager.py" --status-all
        $status = $statusJson | ConvertFrom-Json

        # Count running daemons
        $runningCount = 0
        $deadDaemons = @()

        foreach ($daemon in $status.PSObject.Properties) {
            if ($daemon.Value.running -eq $true) {
                $runningCount++
            } else {
                $deadDaemons += $daemon.Name
            }
        }

        # Log status
        Write-Log "Status: $runningCount/9 daemons running"

        # Restart dead daemons
        if ($deadDaemons.Count -gt 0) {
            Write-Log "ALERT: Found $($deadDaemons.Count) dead daemon(s): $($deadDaemons -join ', ')"

            foreach ($daemon in $deadDaemons) {
                Write-Log "Restarting $daemon..."
                & python "$memoryDir\daemon-manager.py" --start $daemon
                Start-Sleep -Seconds 2
            }

            Write-Log "Restart complete. Verifying..."
            Start-Sleep -Seconds 5

            # Verify restart
            $newStatus = & python "$memoryDir\daemon-manager.py" --status-all | ConvertFrom-Json
            $newRunningCount = ($newStatus.PSObject.Properties | Where-Object { $_.Value.running -eq $true }).Count
            Write-Log "After restart: $newRunningCount/9 daemons running"
        }

    } catch {
        Write-Log "ERROR: Watchdog check failed - $_"
    }

    # Sleep 5 minutes
    Start-Sleep -Seconds 300
}
