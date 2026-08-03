---
description: Close out the cycle with final telemetry and the summary report - owns pipeline Step 8.
---

# release

The release entry point (SRS FR-17). It owns the pipeline's final step.

Ask the user for the task if they did not give one with the command.

## Run it

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/pipeline_entry.py" run release --task "<the task>"
```

Add `--print-only` to see exactly what would run without running it. Add
`--session-id <id>` to run under an existing session rather than a new one. Add
`--engine-root <dir>` if the engine checkout is somewhere the `CWE_ENGINE_ROOT`
environment variable does not already name.

## What it covers

| Step | Name |
|------|------|
| 8 | Final Telemetry & Summary Report |

## Say this plainly, because the name promises more than the step delivers

The source documents name a "release" phase. The pipeline has no release step.
Step 8 is telemetry and a summary report. The work a reader would call releasing
lives in two other places, neither of them reachable from this command:

- the VERSION bump and the CHANGELOG finalisation happen in **Step 7**, which
  the `document` entry point owns;
- tagging and publishing live in the engine's own `scripts/tools/release.py`,
  which is not part of the pipeline graph at all.

Do not describe this command as performing a release. Report what Step 8
actually did, and name the two places above when the user asks where the rest
of it is.

## What it also runs, and why

This entry point is **NOT EXACT**. The engine has one graph entry and no
start-at-step control, so Steps 0 through 7 all run before Step 8 is reached.
In practice this command runs the whole pipeline; `run-pipeline` is the honest
name for that, and it declares it rather than arriving at it. Say so before
running this one.

## Before you report anything

If the first line begins `[UNSAFE]`, relay it verbatim before anything else. The
missing local gate checks a VERSION change on the branch and uncommitted changes
to tracked files, and nothing more; it is not branch protection, and CI still
catches the violation after a push lands. The two ways forward are restoring the
`PreToolUse` entry or running `register-mcp`.

If the command prints `REFUSED:`, relay the reason and stop.

## What to report back

1. The coverage lines, as printed, including the "also perform" list.
2. The summary report the run produced.
3. That this was not a release, and where the release work actually lives.
