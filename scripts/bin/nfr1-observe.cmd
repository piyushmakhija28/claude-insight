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

python -u "%REPO%\tests\nfr1\cli.py" --observe --phase %~1 --from-current-record --skip-leading 1 --plugin-root "%REPO%\plugin" --max-polls 900 --json-out "%~2"
exit /b %ERRORLEVEL%

:usage
echo Usage: nfr1-observe.cmd ^<cold^|warm^> ^<output.json^>
exit /b 2
