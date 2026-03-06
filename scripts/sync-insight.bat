@echo off
REM Selective Sync Script for Claude Insight Repository (Windows)
REM Downloads and syncs only claude-insight components
REM
REM PURPOSE: Quick sync for claude-insight updates
REM This is a convenience wrapper around hook-downloader.py sync-claude-insight
REM
REM USAGE:
REM   sync-insight.bat
REM   sync-insight
REM
REM What it syncs:
REM   - All scripts from claude-insight
REM   - All policies from claude-insight
REM   - Dashboard app (src, templates, static)
REM
REM Version: 1.0.0

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "HOOK_DOWNLOADER=%SCRIPT_DIR%hook-downloader.py"

if not exist "%HOOK_DOWNLOADER%" (
    echo [ERROR] hook-downloader.py not found
    exit /b 1
)

REM Call hook-downloader with selective sync parameter
python "%HOOK_DOWNLOADER%" sync-claude-insight
exit /b %ERRORLEVEL%
