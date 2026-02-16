# Auto-generated daemon startup wrapper
$ErrorActionPreference = "SilentlyContinue"

# Change to memory directory
cd "C:\Users\techd\.claude\memory"

# Start all daemons using startup-hook.sh
& "C:\Program Files\Git\usr\bin\bash.exe" "C:\Users\techd\.claude\memory\startup-hook.sh"

# Log startup
Add-Content -Path "C:\Users\techd\.claude\memory\logs\daemon-startup.log" -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Daemons started via Task Scheduler"
