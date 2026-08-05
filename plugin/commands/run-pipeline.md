---
description: Run the whole SDLC pipeline end to end - Steps 0 through 8, in order.
---

# run-pipeline

The full-pipeline entry point (SRS FR-17). This is the one command that runs
Steps 0 through 8 end to end, and it is the replacement for the behaviour the
`UserPromptSubmit` hook used to give on every prompt.

Ask the user for the task if they did not give one with the command.

## Run it

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/pipeline_entry.py" run run-pipeline --task "<the task>"
```

Add `--print-only` to see exactly what would run without running it. Add
`--engine-root <dir>` if the engine checkout is somewhere the `CWE_ENGINE_ROOT`
environment variable does not already name.

## What it covers

| Step | Name |
|------|------|
| 0 | Pre-Analysis & CallGraph Scan |
| 1 | Task Orchestration & Planning |
| 2 | Issue Tracking |
| 3 | Branch & Workspace Setup |
| 4 | Implementation & Code Generation |
| 5 | Pull Request & Automated Review |
| 6 | Issue & Ticket Closure |
| 7 | Documentation & UML Generation |
| 8 | Final Telemetry & Summary Report |

Coverage is **EXACT**: these nine steps and no others. This is one of only two
entry points that can say that.

## What this command does to the world

It is not read-only and it is not reversible by re-running it. In order, it
creates a GitHub issue, creates a branch, writes code, opens a pull request,
merges it, closes the issue, rewrites documentation and regenerates diagrams.
Step 5 carries a retry loop back to Step 4 on a failed review.

Show the user the `--print-only` output and get their agreement before running
it for real if they have not clearly asked for the whole cycle.

## Before you report anything

If the first line begins `[UNSAFE]`, relay it verbatim before anything else.
This command pushes a branch, so the missing gate is directly in the path: it
checks that a branch carries a VERSION bump and that no tracked changes are
uncommitted. It is not branch protection, and CI still catches the violation,
but only after the push has landed. The two ways forward are restoring the
`PreToolUse` entry or running `register-mcp`.

If the command prints `REFUSED:`, relay the reason and stop. The usual cause is
that the engine checkout could not be located. The plugin never guesses it: an
installed plugin's files sit in the plugin manager's cache with no relationship
to any engine checkout, and the working directory is an unrelated project.

## What to report back

1. The coverage lines, as printed.
2. Every artefact the run created, by identifier: issue, branch, pull request.
3. Whether the Step 5 review passed or exhausted its retries.
4. Which documentation files and diagrams changed.
