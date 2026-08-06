@echo off
REM Run one NFR-1 observer phase against the installed plugin.
REM
REM   nfr1-observe.cmd cold  path\to\out.json
REM   nfr1-observe.cmd warm  path\to\out.json
REM
REM This exists because the full invocation is long enough that pasting it into a
REM terminal breaks the line, which silently drops an argument. It must be launched
REM BY a Claude Code session as a background tool call, not typed into a shell on
REM its own: the observer counts the tool calls that session issues, so with no
REM session driving it there is nothing to count.

setlocal
if "%~1"=="" goto usage
if "%~2"=="" goto usage

set "REPO=%~dp0..\.."
for %%I in ("%REPO%") do set "REPO=%%~fI"

REM 3600 polls at 0.25s is a 15-minute budget. It is generous on purpose: the probe
REM calls must outlive this observer's own startup (Bash spawn, Python boot, psutil
REM import, a 450-process snapshot -- around 20 seconds), and if the harness runs
REM those probes sequentially rather than in parallel their total can reach several
REM minutes. A budget that expires first would report a short count as though the
REM calls had never happened.
python -u "%REPO%\tests\nfr1\cli.py" --observe --phase %~1 --from-current-record --skip-leading 1 --plugin-root "%REPO%\plugin" --max-polls 3600 --json-out "%~2"
exit /b %ERRORLEVEL%

:usage
echo Usage: nfr1-observe.cmd ^<cold^|warm^> ^<output.json^>
exit /b 2
