---
description: Update the documentation and regenerate the diagrams - owns pipeline Step 7.
---

# document

The document entry point (SRS FR-17). It owns the documentation and diagram
generation step.

Ask the user for the task if they did not give one with the command.

## Run it

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/pipeline_entry.py" run document --task "<the task>"
```

Add `--print-only` to see exactly what would run without running it. Add
`--session-id <id>` to run under an existing session rather than a new one. Add
`--engine-root <dir>` if the engine checkout is somewhere the `CWE_ENGINE_ROOT`
environment variable does not already name.

## What it covers

| Step | Name |
|------|------|
| 7 | Documentation & UML Generation |

Step 7 is where `SRS.md`, `CHANGELOG.md`, `README.md` and `CLAUDE.md` are
updated and the thirteen diagram types are regenerated into `uml/` and
`drawio/`. It is also where the VERSION bump and the CHANGELOG finalisation
happen, which is worth stating because a reader looking for that work will
reasonably expect it under `release` and it is not there.

## What it also runs, and why

This entry point is **NOT EXACT**. The engine has one graph entry and no
start-at-step control, so Steps 0 through 6 run before Step 7 is reached, and
Step 8 follows it. Reaching the documentation step therefore also implements,
opens a pull request and closes the issue. Say so before running it.

## Before you report anything

If the first line begins `[UNSAFE]`, relay it verbatim before anything else, and
do not inflate what it means: the missing local gate checks a VERSION change on
the branch and uncommitted changes to tracked files. It is not branch
protection. The two ways forward are restoring the `PreToolUse` entry or running
`register-mcp`.

If the command prints `REFUSED:`, relay the reason and stop.

## What to report back

1. The coverage lines, as printed, including the "also perform" list.
2. Which documentation files changed and which diagram types were regenerated.
3. The VERSION value after the run, if the run reported one.
