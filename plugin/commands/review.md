---
description: Open the pull request, run the automated review and close the issue - owns pipeline Steps 5 and 6.
---

# review

The review entry point (SRS FR-17). It owns the pull-request and closure steps.

Ask the user for the task if they did not give one with the command.

## Run it

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/pipeline_entry.py" run review --task "<the task>"
```

Add `--print-only` to see exactly what would run without running it. Add
`--session-id <id>` to run under an existing session rather than a new one. Add
`--engine-root <dir>` if the engine checkout is somewhere the `CWE_ENGINE_ROOT`
environment variable does not already name.

## What it covers

| Step | Name |
|------|------|
| 5 | Pull Request & Automated Review |
| 6 | Issue & Ticket Closure |

Step 6 sits here rather than under `document` because closure is the completion
of the merge, not a documentation act: the issue closes and the Jira ticket
moves to Done once the pull request lands.

## What it also runs, and why

This entry point is **NOT EXACT**. The engine has one graph entry and no
start-at-step control, so Steps 0 through 4 run before Step 5 is reached, and
Steps 7 and 8 follow after Step 6. Reaching the review step therefore also
implements. Say so before running it.

Step 5 carries a retry loop: a failed review routes back to Step 4 and the
implementation is re-run until it passes or the retry budget is spent. Report
which of the two happened rather than reporting only the final state.

## Before you report anything

If the first line begins `[UNSAFE]`, relay it verbatim before anything else. It
matters more here than anywhere: this entry point pushes a branch, and the
missing gate is the one that checks a VERSION bump and uncommitted tracked
changes before a push. It is still not branch protection, and CI still catches
the violation after the push lands. The two ways forward are restoring the
`PreToolUse` entry or running `register-mcp`.

If the command prints `REFUSED:`, relay the reason and stop.

## What to report back

1. The coverage lines, as printed, including the "also perform" list.
2. The pull request the run opened, and whether the review passed or exhausted
   its retries.
3. Whether the issue was closed.
