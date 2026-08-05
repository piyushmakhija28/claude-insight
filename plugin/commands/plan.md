---
description: Plan and decompose a task - runs pipeline Steps 0 and 1 and stops before anything is tracked or branched.
---

# plan

The plan/decompose entry point (SRS FR-17). It runs the pipeline's analysis and
planning steps and stops: no GitHub issue, no Jira ticket, no branch, no code.

Ask the user for the task if they did not give one with the command.

## Run it

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/pipeline_entry.py" run plan --task "<the task>"
```

Add `--print-only` to see exactly what would run without running it. Add
`--engine-root <dir>` if the engine checkout is somewhere the `CWE_ENGINE_ROOT`
environment variable does not already name.

## What it covers

| Step | Name |
|------|------|
| 0 | Pre-Analysis & CallGraph Scan |
| 1 | Task Orchestration & Planning |

This is one of only two entry points whose coverage is **EXACT** - the engine
performs these steps and no others. Steps 2 and 3 are entered and return
immediately without doing their work, because the command dispatches with the
engine's dry-run control.

## Before you report anything

The command prints its own coverage lines. Read them, do not restate them from
memory, and relay them as written.

If the first line begins `[UNSAFE]`, relay it verbatim before anything else. It
means nothing on this machine checks that a branch carries a VERSION bump or
that tracked changes are committed before a push. It is not branch protection
and must not be described as one; CI still enforces the rule, but only after a
push has landed. The two ways forward are restoring the `PreToolUse` entry or
running `register-mcp`. Silence means the gate is in place - do not invent
reassurance for it.

If the command prints `REFUSED:`, relay the reason and stop. The usual cause is
that the engine checkout could not be located, which the plugin never guesses:
an installed plugin's files sit in the plugin manager's cache with no
relationship to any engine checkout, and the working directory is an unrelated
project.

## What to report back

1. The coverage lines, as printed.
2. Where the generated plan was written, if the run reported a path.
3. That `implement` is the next entry point, and that it is **not** exact -
   the engine exposes no start-at-step control, so it re-enters Steps 0 and 1
   and continues past Step 4 to Step 8.

Do not run `implement` on the user's behalf as a result of this command.
Planning is not implementing, and that decision is the user's.
