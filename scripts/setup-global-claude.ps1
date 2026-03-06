# =============================================================================
# Claude Insight - Global Claude Memory System Setup (Windows PowerShell)
# =============================================================================
# This script sets up the Claude Memory System (3-Level Architecture) in your
# ~/.claude directory so Claude Code follows enforcement policies automatically.
#
# Run from PowerShell:
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#   .\scripts\setup-global-claude.ps1
# =============================================================================

$ErrorActionPreference = "Continue"

$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$ClaudeDir   = Join-Path $env:USERPROFILE ".claude"
$MemoryCurrent = Join-Path $ClaudeDir "memory\current"
$SettingsFile  = Join-Path $ClaudeDir "settings.json"
$GlobalClaudeMd = Join-Path $ClaudeDir "CLAUDE.md"

Write-Host ""
Write-Host "============================================================"
Write-Host " Claude Insight - Global Memory System Setup (Windows)"
Write-Host "============================================================"
Write-Host ""

# Step 1: Create ~/.claude directory structure
Write-Host "[1/5] Setting up ~/.claude directory..."
$dirs = @(
    $ClaudeDir,
    $MemoryCurrent,
    (Join-Path $ClaudeDir "memory\logs\sessions"),
    (Join-Path $ClaudeDir "memory\sessions"),
    (Join-Path $ClaudeDir "skills"),
    (Join-Path $ClaudeDir "agents"),
    (Join-Path $ClaudeDir "hooks")
)
foreach ($d in $dirs) {
    if (-not (Test-Path $d)) {
        New-Item -ItemType Directory -Path $d -Force | Out-Null
    }
}
Write-Host "[OK] ~/.claude directory structure ready"

# Step 2: Copy core enforcement scripts
Write-Host "[2/5] Installing core enforcement scripts..."

$scriptsToCopy = @(
    "auto-fix-enforcer.sh",
    "auto-enforce-all-policies.sh",
    "session-start.sh",
    "per-request-enforcer.py",
    "context-monitor-v2.py",
    "blocking-policy-enforcer.py",
    "session-id-generator.py",
    "session-id-generator.sh",
    "session-logger.py",
    "detect-sync-eligibility.py",
    "3-level-flow.py",
    "clear-session-handler.py",
    "stop-notifier.py",
    "pre-tool-enforcer.py",
    "post-tool-tracker.py"
)

$copied = 0
$skipped = 0

foreach ($script in $scriptsToCopy) {
    $src = Join-Path $ScriptDir $script
    $dst = Join-Path $MemoryCurrent $script
    if (Test-Path $src) {
        Copy-Item $src $dst -Force
        Write-Host "  [OK] $script"
        $copied++
    } else {
        Write-Host "  [SKIP] $script (not found)"
        $skipped++
    }
}
Write-Host "[OK] $copied scripts copied, $skipped skipped"

# Step 3: Install global CLAUDE.md
Write-Host "[3/5] Installing global CLAUDE.md..."

$template = Join-Path $ScriptDir "global-claude-md-template.md"

if (Test-Path $GlobalClaudeMd) {
    Write-Host "  [INFO] Existing ~/.claude/CLAUDE.md found"
    $existing = Get-Content $GlobalClaudeMd -Raw

    if ($existing -match "HARDCODED 3-LEVEL ARCHITECTURE") {
        Write-Host "  [OK] Global CLAUDE.md already has 3-level architecture - keeping existing"
    } else {
        Write-Host "  [INFO] Backing up to ~/.claude/CLAUDE.md.backup"
        Copy-Item $GlobalClaudeMd "$GlobalClaudeMd.backup" -Force

        if (Test-Path $template) {
            Write-Host "  [INFO] Merging 3-level architecture into existing CLAUDE.md"
            $templateContent = Get-Content $template -Raw
            $merged = $templateContent + "`n`n---`n# YOUR EXISTING CONFIGURATION`n---`n`n" + $existing
            Set-Content $GlobalClaudeMd $merged -Encoding UTF8
            Write-Host "  [OK] 3-level architecture merged"
        }
    }
} else {
    if (Test-Path $template) {
        Copy-Item $template $GlobalClaudeMd -Force
        Write-Host "  [OK] Global CLAUDE.md installed from template"
    } else {
        Write-Host "  [WARN] Template not found - creating minimal CLAUDE.md"
        Set-Content $GlobalClaudeMd "# Claude Memory System`nInstall claude-insight for full setup.`nSee: https://github.com/piyushmakhija28/claude-insight" -Encoding UTF8
    }
}

# Step 4: Install hooks in settings.json
Write-Host "[4/5] Installing hooks in ~/.claude/settings.json..."

$hookCmd3Level   = "python " + (Join-Path $MemoryCurrent "3-level-flow.py") + " --summary"
$hookCmdClear    = "python " + (Join-Path $MemoryCurrent "clear-session-handler.py")
$hookCmdStop     = "python " + (Join-Path $MemoryCurrent "stop-notifier.py")
$hookCmdPreTool  = "python " + (Join-Path $MemoryCurrent "pre-tool-enforcer.py")
$hookCmdPostTool = "python " + (Join-Path $MemoryCurrent "post-tool-tracker.py")

if (Test-Path $SettingsFile) {
    $settingsContent = Get-Content $SettingsFile -Raw
    if ($settingsContent -match "3-level-flow") {
        Write-Host "  [OK] Hooks already in settings.json - skipping"
        if ($settingsContent -notmatch "PreToolUse") {
            Write-Host "  [WARN] PreToolUse and PostToolUse hooks may be missing"
            Write-Host "  [INFO] Add pre-tool-enforcer.py and post-tool-tracker.py manually to settings.json"
        }
    } else {
        Write-Host "  [WARN] settings.json exists but no hooks found"
        Write-Host "  [INFO] See README.md 'How the Hooks Work' section for manual setup"
    }
} else {
    $settingsJson = @{
        model = "sonnet"
        hooks = @{
            UserPromptSubmit = @(
                @{
                    hooks = @(
                        @{
                            type = "command"
                            command = $hookCmdClear
                            timeout = 15
                            statusMessage = "Level 1: Checking session state..."
                        },
                        @{
                            type = "command"
                            command = $hookCmd3Level
                            timeout = 30
                            statusMessage = "Level -1/1/2/3: Running 3-level architecture check..."
                        }
                    )
                }
            )
            PreToolUse = @(
                @{
                    hooks = @(
                        @{
                            type = "command"
                            command = $hookCmdPreTool
                            timeout = 10
                            statusMessage = "Level 3.6/3.7: Tool optimization + failure prevention..."
                        }
                    )
                }
            )
            PostToolUse = @(
                @{
                    hooks = @(
                        @{
                            type = "command"
                            command = $hookCmdPostTool
                            timeout = 10
                            statusMessage = "Level 3.9: Tracking task progress..."
                        }
                    )
                }
            )
            Stop = @(
                @{
                    hooks = @(
                        @{
                            type = "command"
                            command = $hookCmdStop
                            timeout = 20
                            statusMessage = "Level 3.10: Session save + voice notification..."
                        }
                    )
                }
            )
        }
    }
    $settingsJson | ConvertTo-Json -Depth 10 | Set-Content $SettingsFile -Encoding UTF8
    Write-Host "  [OK] settings.json created with all 4 hooks (UserPromptSubmit + PreToolUse + PostToolUse + Stop)"
}

# Step 5: Finalize
Write-Host "[5/5] Finalizing..."
Set-Content (Join-Path $MemoryCurrent "VERSION") "1.0.0" -Encoding UTF8

$manifestContent = @"
Claude Insight Memory System v1.0.0
Installed: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Platform: Windows

Core Scripts:
  - 3-level-flow.py (main hook entry)
  - auto-fix-enforcer.sh (Level -1)
  - session-start.sh (Level 1)
  - per-request-enforcer.py (policy enforcement)
  - context-monitor-v2.py (context tracking)
  - blocking-policy-enforcer.py (blocking enforcement)
  - session-id-generator.py/.sh (session tracking)
  - session-logger.py (logging)
  - clear-session-handler.py (session clear hook)
  - stop-notifier.py (stop hook)
"@
Set-Content (Join-Path $MemoryCurrent "MANIFEST.md") $manifestContent -Encoding UTF8

Write-Host ""
Write-Host "============================================================"
Write-Host " Setup Complete!"
Write-Host "============================================================"
Write-Host ""
Write-Host " Installed to: $ClaudeDir"
Write-Host " Core scripts: $MemoryCurrent"
Write-Host " Global CLAUDE.md: $GlobalClaudeMd"
Write-Host " Settings: $SettingsFile"
Write-Host ""
Write-Host " NEXT STEPS:"
Write-Host "  1. Restart Claude Code (close and reopen)"
Write-Host "  2. The 3-level architecture will run automatically"
Write-Host "     on every message you send"
Write-Host ""
Write-Host " IMPORTANT:"
Write-Host "  - Global CLAUDE.md has the 3-level architecture rules"
Write-Host "  - Do NOT add project-specific info to ~/.claude/CLAUDE.md"
Write-Host "  - Add project info to your PROJECT's CLAUDE.md instead"
Write-Host "  - Project CLAUDE.md adds context but cannot override global policies"
Write-Host ""
