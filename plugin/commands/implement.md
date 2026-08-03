---
description: Track, branch and implement a task - owns pipeline Steps 2, 3 and 4.
---

# implement

The implement entry point (SRS FR-17). It owns the steps that turn a plan into
tracked, branched, written code.

Ask the user for the task if they did not give one with the command.

## Run it

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/pipeline_entry.py" run implement --task "<the task>"
```

Add `--print-only` to see exactly what would run without running it. Add
`--session-id <id>` to run under an existing session rather than a new one. Add
`--engine-root <dir>` if the engine checkout is somewhere the `CWE_ENGINE_ROOT`
environment variable does not already name.

## What it covers

| Step | Name |
|------|------|
| 2 | Issue Tracking |
| 3 | Branch & Workspace Setup |
| 4 | Implementation & Code Generation |

## What it also runs, and why

This entry point is **NOT EXACT**, and the command says so on every invocation.
The engine has one graph entry and no start-at-step control, so reaching Step 2
means Steps 0 and 1 run first, and there is no stop point between Step 4 and
Step 8 - so Steps 5 through 8 follow. The practical consequence is that this
command creates a pull request, closes the issue and writes documentation as
well as implementing.

State that plainly before running it. A user who expected this to stop after
writing code needs to know it does not, and the `--print-only` flag exists so
they can see the whole shape first.

## Before you report anything

If the first line begins `[UNSAFE]`, relay it verbatim before anything else, and
be precise about its scope: the missing local gate checks two things, a VERSION
change somewhere on the branch and no uncommitted changes to tracked files. It
is not branch protection. CI still catches a non-compliant push, but only after
it has landed. The two ways forward are restoring the `PreToolUse` entry or
running `register-mcp`.

If the command prints `REFUSED:`, relay the reason and stop.

## What to report back

1. The coverage lines, as printed, including the "also perform" list.
2. The issue and branch the run created, if it reported them.
3. Which files were changed.
